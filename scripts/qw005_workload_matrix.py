#!/usr/bin/env python3
"""
QW-005: Agent Workload Matrix
Produce a heatmap showing tickets completed per agent per calendar week.

Input: ~/fleet/analytics/standup_data.json (from QW-001)
Output:
  - ~/fleet/analytics/charts/workload_matrix.html
  - ~/fleet/analytics/workload_matrix.json

Charts:
1. Heatmap: X-axis = ISO week, Y-axis = agent, color = ticket count
   (white=0, light blue=1-2, mid blue=3-5, dark blue=6+)
2. Stacked area chart: cumulative tickets closed per agent over time
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics

# Constants
INPUT_FILE = Path("/Users/miguelrodriguez/fleet/analytics/standup_data.json")
OUTPUT_DIR = Path("/Users/miguelrodriguez/fleet/analytics/charts")
HTML_FILE = OUTPUT_DIR / "workload_matrix.html"
JSON_FILE = OUTPUT_DIR / "workload_matrix.json"

# Known agents
AGENTS = ['clau', 'codi', 'gem', 'misty', 'gemma']

# Color scale for heatmap
COLOR_SCALE = {
    0: '#ffffff',  # white
    1: '#dbeafe',  # light blue
    2: '#bfdbfe',  # medium-light blue
    3: '#60a5fa',  # medium blue
    5: '#3b82f6',  # blue
    7: '#2563eb',  # dark blue
    10: '#1d4ed8',  # darker blue
}


def get_iso_week(date_str):
    """Get ISO week number and year from date string."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        year, week, _ = date.isocalendar()
        return f"{year}-W{week:02d}"
    except:
        return None


def get_color_for_count(count):
    """Get color for a ticket count based on the scale."""
    if count == 0:
        return COLOR_SCALE[0]
    elif count <= 2:
        return COLOR_SCALE[1]
    elif count <= 5:
        return COLOR_SCALE[3]
    elif count <= 7:
        return COLOR_SCALE[5]
    else:
        return COLOR_SCALE[10]


def main():
    print("QW-005: Agent Workload Matrix")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load standup data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} entries from {INPUT_FILE}")
    
    # Count tickets per agent per week
    # First, get all dates and their weeks
    date_to_week = {}
    for entry in data:
        date = entry.get('date')
        if date:
            date_to_week[date] = get_iso_week(date)
    
    # Count tickets per agent per week
    weekly_counts = defaultdict(lambda: defaultdict(int))
    for entry in data:
        agent = entry.get('agent')
        date = entry.get('date')
        if not agent or not date:
            continue
        
        week = date_to_week.get(date)
        if not week:
            continue
        
        # Count tasks completed
        tasks = entry.get('tasks_completed', [])
        weekly_counts[agent][week] += len(tasks)
    
    # Get all weeks
    all_weeks = sorted(set(
        week for agent_data in weekly_counts.values()
        for week in agent_data.keys()
    ))
    
    print(f"Weeks: {len(all_weeks)} ({all_weeks[0]} to {all_weeks[-1]})")
    
    # Ensure all agents have all weeks
    for agent in AGENTS:
        for week in all_weeks:
            if week not in weekly_counts[agent]:
                weekly_counts[agent][week] = 0
    
    # Prepare heatmap data
    heatmap_data = {
        'weeks': all_weeks,
        'agents': AGENTS,
        'counts': {
            agent: {week: weekly_counts[agent][week] for week in all_weeks}
            for agent in AGENTS
        }
    }
    
    # Prepare cumulative data for stacked area chart
    # Sort dates chronologically
    all_dates = sorted(date_to_week.keys())
    
    cumulative_data = {agent: [] for agent in AGENTS}
    current_totals = {agent: 0 for agent in AGENTS}
    
    for date in all_dates:
        week = date_to_week[date]
        for agent in AGENTS:
            count = weekly_counts[agent].get(week, 0)
            current_totals[agent] += count
            cumulative_data[agent].append(current_totals[agent])
    
    cumulative_chart_data = {
        'dates': all_dates,
        'agents': AGENTS,
        'cumulative': cumulative_data
    }
    
    # Output JSON
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'heatmap': heatmap_data,
        'cumulative': cumulative_chart_data,
        'statistics': {
            'total_weeks': len(all_weeks),
            'total_tickets': sum(
                sum(weekly_counts[agent].values())
                for agent in AGENTS
            ),
            'agents': AGENTS
        }
    }
    
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✓ JSON written to {JSON_FILE}")
    
    # Generate HTML
    html = generate_html(heatmap_data, cumulative_chart_data)
    
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ HTML written to {HTML_FILE}")
    print(f"✓ HTML size: {HTML_FILE.stat().st_size} bytes")
    
    return 0


def generate_html(heatmap_data, cumulative_data):
    """Generate HTML with heatmap and cumulative charts."""
    
    weeks = heatmap_data['weeks']
    agents = heatmap_data['agents']
    
    # Heatmap chart - We'll use a bar chart with grouped bars as a heatmap approximation
    # Or we can use a bubble chart. Actually, let's create an HTML table with colored cells.
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Workload Matrix - Fleet Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background: #f9fafb;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #111827;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #374151;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .subtitle {{
            color: #6b7280;
            margin-bottom: 20px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        canvas {{
            max-height: 500px;
        }}
        .heatmap-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .heatmap-table th {{
            padding: 10px;
            text-align: center;
            background: #f9fafb;
            font-size: 11px;
            border: 1px solid #e5e7eb;
        }}
        .heatmap-table td {{
            padding: 10px;
            text-align: center;
            border: 1px solid #e5e7eb;
            font-size: 11px;
            min-width: 25px;
        }}
        .heatmap-table tr:first-child th {{
            position: sticky;
            top: 0;
            background: white;
        }}
        .heatmap-table th:first-child {{
            position: sticky;
            left: 0;
            background: #f9fafb;
            z-index: 10;
        }}
        .footer {{
            color: #6b7280;
            font-size: 12px;
            margin-top: 30px;
        }}
        .agent-col {{
            font-weight: 600;
            background: #f9fafb !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Agent Workload Matrix</h1>
        <p class="subtitle">Tickets completed per agent per ISO week</p>
        
        <div class="card">
            <h2>📊 Heatmap: Tickets per Agent per Week</h2>
            <p style="color: #6b7280; font-size: 14px; margin-bottom: 15px;">
                Color intensity = ticket count. White = 0, Light blue = 1-2, Medium blue = 3-5, Dark blue = 6+.
            </p>
            <div style="overflow-x: auto;">
                <table class="heatmap-table">
                    <thead>
                        <tr>
                            <th>Agent / Week</th>
"""
    
    for week in weeks:
        html += f"""                            <th>{week}</th>
"""
    
    html += """                        </tr>
                    </thead>
                    <tbody>
"""
    
    for agent in agents:
        html += f"""                        <tr>
                            <td class="agent-col">{agent.upper()}</td>
"""
        for week in weeks:
            count = heatmap_data['counts'][agent][week]
            color = get_color_for_count(count)
            html += f"""                            <td style="background-color: {color};" title="{count} tickets">{count}</td>
"""
        html += """                        </tr>
"""
    
    html += """                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card">
            <h2>📈 Cumulative Tickets per Agent Over Time</h2>
            <p style="color: #6b7280; font-size: 14px; margin-bottom: 15px;">
                Stacked area chart showing who carried the sprint at what point.
            </p>
            <canvas id="cumulativeChart"></canvas>
        </div>
        
        <div class="footer">
            Generated from standup_data.json | QW-005
        </div>
    </div>
    
    <script>
        const AGENT_COLORS = {
            'clau': '#ef4444',
            'codi': '#3b82f6',
            'gem': '#10b981',
            'misty': '#8b5cf6',
            'gemma': '#f59e0b'
        };
        
        const cumulativeData = {cumulative_data_json};
        
        const cumulativeCtx = document.getElementById('cumulativeChart');
        
        const datasets = cumulativeData.agents.map(agent => ({
            label: agent.toUpperCase(),
            data: cumulativeData.cumulative[agent],
            borderColor: AGENT_COLORS[agent],
            backgroundColor: AGENT_COLORS[agent] + '40',
            borderWidth: 2,
            fill: true
        }));
        
        new Chart(cumulativeCtx, {
            type: 'line',
            data: {
                labels: cumulativeData.dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.raw + ' tickets';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Cumulative Tickets'
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
    
    # Inject cumulative data as JSON
    import json as json_module
    cumulative_data_json = json_module.dumps(cumulative_data)
    html = html.replace('{cumulative_data_json}', cumulative_data_json)
    
    return html


if __name__ == "__main__":
    exit(main())
