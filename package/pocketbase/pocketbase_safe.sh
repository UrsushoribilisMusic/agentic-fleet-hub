#!/bin/bash
# pocketbase_safe.sh
# Hardened startup wrapper for PocketBase to prevent duplicate listeners and lock contention.
# Supports: start (default), stop, status, restart

PB_DIR="${FLOTILLA_PB_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
PB_BINARY="$PB_DIR/pocketbase"
PB_DATA="$PB_DIR/pb_data"
PORT="${FLOTILLA_PB_PORT:-8090}"
LOG_DIR="${FLOTILLA_LOG_DIR:-$PB_DIR/../scripts/logs}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/pocketbase_wrapper.log"
LOCKDIR="$PB_DATA/pocketbase_wrapper.lockdir"
LOCKFILE="$PB_DATA/pocketbase_wrapper.pid"
MAX_LOG_SIZE_GB=1

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WRAPPER] $1" | tee -a "$LOG_FILE"
}

get_pids_by_port() {
    lsof -t -nP -iTCP:$PORT -sTCP:LISTEN
}

get_pids_by_data() {
    # Check for any process accessing the data directory (SQLite files)
    lsof -t +D "$PB_DATA" 2>/dev/null | sort -u
}

get_pids_by_ps() {
    # Find all pocketbase serve processes excluding current wrapper PID and its children
    pgrep -f "pocketbase serve" | grep -v "$$"
}

check_logs_size() {
    local logs_db="$PB_DATA/logs.db"
    if [ -f "$logs_db" ]; then
        local size_bytes=$(stat -f%z "$logs_db" 2>/dev/null || stat -c%s "$logs_db" 2>/dev/null)
        local size_gb=$((size_bytes / 1024 / 1024 / 1024))
        if [ "$size_gb" -ge "$MAX_LOG_SIZE_GB" ]; then
            log "WARNING: logs.db is $size_gb GB (Threshold: $MAX_LOG_SIZE_GB GB). This may cause high CPU usage."
            log "Consider running: ./pocketbase_safe.sh clean-logs"
        fi
    fi
}

clean_logs() {
    log "Initiating logs cleanup..."
    stop
    local logs_db="$PB_DATA/logs.db"
    if [ -f "$logs_db" ]; then
        log "Removing $logs_db..."
        rm "$logs_db"
        log "Logs database removed. It will be recreated on next start."
    else
        log "No logs.db found to clean."
    fi
    
    if launchctl list fleet.pocketbase > /dev/null 2>&1; then
        log "Restarting via launchctl..."
        launchctl start fleet.pocketbase
    else
        log "Restarting via start command..."
        start
    fi
}

status() {
    local port_pids=$(get_pids_by_port)
    local data_pids=$(get_pids_by_data)
    local ps_pids=$(get_pids_by_ps)
    
    if [ -n "$port_pids" ] || [ -n "$data_pids" ] || [ -n "$ps_pids" ]; then
        echo "PocketBase Status: RUNNING"
        [ -n "$port_pids" ] && echo "  Listening on port $PORT (PIDs: $(echo $port_pids | tr '\n' ' '))"
        [ -n "$data_pids" ] && echo "  Accessing data directory (PIDs: $(echo $data_pids | tr '\n' ' '))"
        [ -n "$ps_pids" ] && echo "  Found via ps (PIDs: $(echo $ps_pids | tr '\n' ' '))"
        
        if [ -d "$LOCKDIR" ]; then
            echo "  Lock directory exists (PID: $(cat "$LOCKFILE" 2>/dev/null || echo 'unknown'))"
        else
            echo "  WARNING: No lock directory found but processes are running."
        fi
        check_logs_size
        return 0
    else
        echo "PocketBase Status: STOPPED"
        check_logs_size
        return 1
    fi
}

stop() {
    log "Stopping PocketBase and clearing all related processes..."
    # Collect all PIDs into a space-separated list for easy iteration
    local all_pids=$( (get_pids_by_port; get_pids_by_data; get_pids_by_ps) | sort -u | tr '\n' ' ' )
    
    if [ -n "$all_pids" ]; then
        for pid in $all_pids; do
            log "Sending SIGTERM to PID $pid..."
            kill "$pid" 2>/dev/null
        done
        
        sleep 2
        
        # Check again and SIGKILL if necessary
        all_pids=$( (get_pids_by_port; get_pids_by_data; get_pids_by_ps) | sort -u | tr '\n' ' ' )
        if [ -n "$all_pids" ]; then
            for pid in $all_pids; do
                log "WARNING: PID $pid still running. Sending SIGKILL..."
                kill -9 "$pid" 2>/dev/null
            done
        fi
    fi
    
    if [ -d "$LOCKDIR" ]; then
        log "Removing lock directory..."
        rm -rf "$LOCKDIR"
    fi
    log "Stop sequence complete."
}

start() {
    log "Starting safety checks for PocketBase..."

    # 1. Check for rogue processes on port or data BEFORE taking lock
    # This ensures we can clear processes that might have been started without the wrapper
    local port_pids=$(get_pids_by_port)
    local data_pids=$(get_pids_by_data)
    local ps_pids=$(get_pids_by_ps)
    local all_conflicts=$(echo -e "$port_pids\n$data_pids\n$ps_pids" | grep . | sort -u | tr '\n' ' ')

    if [ -n "$all_conflicts" ]; then
        log "PRE-START CONFLICT: Port $PORT or data directory is in use by PIDs: $all_conflicts"
        
        # Identify holder of the lock if it exists
        local holder_pid=$(cat "$LOCKFILE" 2>/dev/null || echo "none")
        
        # Check if any conflict is NOT the holder of the current lock
        local rogue_found=false
        for pid in $all_conflicts; do
            if [ "$pid" != "$holder_pid" ]; then
                rogue_found=true
                local proc_info=$(ps -p "$pid" -o user,comm,args= 2>/dev/null)
                log "ROGUE PROCESS DETECTED: PID $pid - $proc_info"
                
                if [[ "$proc_info" == *"docker"* ]] || [[ "$proc_info" == *"com.docker"* ]]; then
                    log "WARNING: This is a Docker process. Attempting to kill it may fail or disrupt other containers."
                    log "Recommended action: 'docker compose down' in the project directory."
                fi
            fi
        done

        if [ "$rogue_found" = true ]; then
            log "Attempting to clear rogue processes automatically (SIGTERM)..."
            for pid in $all_conflicts; do
                if [ "$pid" != "$holder_pid" ]; then
                    kill "$pid" 2>/dev/null
                fi
            done
            sleep 2
            
            # Re-check
            port_pids=$(get_pids_by_port)
            data_pids=$(get_pids_by_data)
            pb_ps_pids=$(get_pids_by_ps)
            local remaining=$(echo -e "$port_pids\n$data_pids\n$pb_ps_pids" | grep . | grep -v "$holder_pid" | sort -u)
            
            if [ -n "$remaining" ]; then
                log "ROGUE PROCESSES PERSIST: Escalating to SIGKILL..."
                for pid in $remaining; do
                    kill -9 "$pid" 2>/dev/null
                done
                sleep 2
                
                # Final re-check - if still there, we MUST fail
                local dead_serious=$(echo -e "$(get_pids_by_port)\n$(get_pids_by_data)\n$(get_pids_by_ps)" | grep . | grep -v "$holder_pid" | sort -u)
                if [ -n "$dead_serious" ]; then
                    log "CRITICAL: Could not clear rogue processes: $dead_serious. Manual intervention required."
                    exit 1
                fi
            fi
        fi
    fi

    # 2. Atomic locking using mkdir
    if ! mkdir "$LOCKDIR" 2>/dev/null; then
        local holder_pid=$(cat "$LOCKFILE" 2>/dev/null || echo "unknown")
        local holder_proc=$(ps -p "$holder_pid" -o comm= 2>/dev/null)
        
        # Check if holder exists AND is actually a PocketBase or wrapper process
        if [ "$holder_pid" != "unknown" ] && \
           [[ "$holder_proc" == *"pocketbase"* || "$holder_proc" == *"bash"* || "$holder_proc" == *"sh"* ]]; then
            log "LOCK CONFLICT: Another instance holds the lock (PID: $holder_pid, Name: $holder_proc)."
            # If the holder is actually running on our port/data, we must exit
            if echo "$all_conflicts" | grep -qw "$holder_pid"; then
                log "Confirmed: PID $holder_pid is active and healthy on our resources. Exiting."
                exit 1
            else
                log "WARNING: PID $holder_pid holds the lock but is NOT on port/data. It might be starting up or hung."
                log "Wait 5 seconds and retry manually if this persists."
                exit 1
            fi
        else
            log "Detected stale lock directory (PID $holder_pid not running or not PocketBase). Cleaning up..."
            rm -rf "$LOCKDIR"
            mkdir "$LOCKDIR" || { log "CRITICAL: Failed to recreate lock directory."; exit 1; }
        fi
    fi
    echo "$$" > "$LOCKFILE"

    # 3. Final verification of port and data
    local final_port=$(get_pids_by_port)
    local final_data=$(get_pids_by_data)
    if [ -n "$final_port" ] && [ "$final_port" != "$$" ]; then
        log "ERROR: Port $PORT still in use by PID $final_port after lock acquisition."
        rm -rf "$LOCKDIR"
        exit 1
    fi
    if [ -n "$final_data" ] && [ "$final_data" != "$$" ]; then
        # On macOS, lsof might show current shell script (us) accessing the dir
        # We filter out our own PID
        local real_conflicts=$(echo "$final_data" | grep -v "$$")
        if [ -n "$real_conflicts" ]; then
            log "ERROR: Data directory still in use by PIDs: $real_conflicts after lock acquisition."
            rm -rf "$LOCKDIR"
            exit 1
        fi
    fi

    # 5. Pre-flight log size check
    check_logs_size

    # 6. Exec PocketBase
    log "All checks passed. Starting PocketBase via binary interceptor..."
    export POCKETBASE_WRAPPER_ACTIVE=1
    exec "$PB_BINARY" serve --dir "$PB_DATA" --migrationsDir "$PB_DIR/pb_migrations" --http "${FLOTILLA_PB_BIND:-127.0.0.1}:$PORT"
}

case "$1" in
    status)
        status
        ;;
    stop)
        stop
        ;;
    clean-logs)
        clean_logs
        ;;
    restart)
        if launchctl list fleet.pocketbase >/dev/null 2>&1; then
            log "Service managed by launchctl. Initiating managed restart..."
            launchctl stop fleet.pocketbase
            sleep 3
            # KeepAlive should restart it, but we'll try to start it just in case or if it's throttled
            launchctl start fleet.pocketbase
            sleep 2
            status
        else
            log "Service NOT managed by launchctl. Performing manual restart..."
            stop
            sleep 1
            start
        fi
        ;;
    start|*)
        start
        ;;
esac
