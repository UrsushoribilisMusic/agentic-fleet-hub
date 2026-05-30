#!/usr/bin/env python3
"""
QW-002: Tickets-per-day Chart
Using standup_data.json, produce a grouped bar chart of tickets worked on per day,
color-coded by project prefix (SC, PC, CR, fleet, QW, other).

Output:
- ~/fleet/analytics/charts/tickets_per_day.html (standalone HTML with Chart.js)
- ~/fleet/analytics/charts/tickets_per_day.json (raw data)

Color scheme:
- SC = indigo (#4f46e5)
- PC = teal (#14b8a6)
- CR = amber (#f59e0b)
- fleet = blue (#3b82f6)
- QW = purple (#8b5cf6)
- other = grey (#6b7280)
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

# Constants
STANDUP_DATA_FILE = Path("/Users/miguelrodriguez/fleet/analytics/standup_data.json")
OUTPUT_DIR = Path("/Users/miguelrodriguez/fleet/analytics/charts")
OUTPUT_HTML = OUTPUT_DIR / "tickets_per_day.html"
OUTPUT_JSON = OUTPUT_DIR / "tickets_per_day.json"

# Project colors
PROJECT_COLORS = {
    "SC": "#4f46e5",  # indigo
    "PC": "#14b8a6",  # teal
    "CR": "#f59e0b",  # amber
    "fleet": "#3b82f6",  # blue
    "QW": "#8b5cf6",  # purple
    "RT": "#06b6d4",  # cyan
    "other": "#6b7280",  # grey
}

def load_standup_data() -> List[Dict[str, Any]]:
    """Load standup data from JSON file"""
    with open(STANDUP_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_tickets_per_day(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Count tickets per day per project.
    Returns: {date: {project: count}}
    """
    daily_counts = defaultdict(lambda: defaultdict(int))
    
    for entry in entries:
        date = entry.get("date", "")
        for task in entry.get("tasks_completed", []):
            project = task.get("project", "other")
            daily_counts[date][project] += 1
    
    return daily_counts

def prepare_chart_data(daily_counts: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """Prepare data for Chart.js stacked bar chart"""
    # Get all dates in order
    dates = sorted(daily_counts.keys())
    
    # Get all projects
    all_projects = set()
    for date in dates:
        for project in daily_counts[date].keys():
            all_projects.add(project)
    
    # Sort projects by color priority
    project_order = ["SC", "PC", "CR", "RT", "fleet", "QW", "other"]
    ordered_projects = [p for p in project_order if p in all_projects]
    # Add any remaining projects at the end
    for p in sorted(all_projects - set(ordered_projects)):
        ordered_projects.append(p)
    
    # Build datasets for Chart.js (one dataset per project)
    datasets = []
    for project in ordered_projects:
        color = PROJECT_COLORS.get(project, "#6b7280")
        data = [daily_counts[date].get(project, 0) for date in dates]
        datasets.append({
            "label": project,
            "data": data,
            "backgroundColor": color,
            "borderColor": color,
            "borderWidth": 1
        })
    
    return {
        "dates": dates,
        "projects": ordered_projects,
        "datasets": datasets
    }

def generate_html(chart_data: Dict[str, Any]) -> str:
    """Generate standalone HTML with Chart.js"""
    dates = chart_data["dates"]
    datasets = chart_data["datasets"]
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fleet Analytics - Tickets per Day</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0f172a;
            color: #e2e8f0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #fff;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #94a3b8;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        canvas {{
            max-height: 600px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #1e293b;
            border-radius: 8px;
            padding: 15px 20px;
            color: #fff;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #3b82f6;
        }}
        .stat-label {{
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Fleet Analytics: Tickets per Day</h1>
        <p class="subtitle">Tickets worked on per day, grouped by project</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(dates)}</div>
                <div class="stat-label">Days</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(sum(d['data']) for d in datasets)}</div>
                <div class="stat-label">Total Tickets</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(datasets)}</div>
                <div class="stat-label">Projects</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="ticketsPerDayChart"></canvas>
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('ticketsPerDayChart');
        
        const data = {{
            labels: {json.dumps(dates)},
            datasets: {json.dumps(datasets, indent=2)}
        }};
        
        const config = {{
            type: 'bar',
            data: data,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        title: {{
                            display: true,
                            text: 'Date',
                            color: '#94a3b8'
                        }},
                        ticks: {{
                            color: '#e2e8f0',
                            maxRotation: 45,
                            minRotation: 45
                        }},
                        grid: {{
                            color: '#334155'
                        }}
                    }},
                    y: {{
                        stacked: true,
                        title: {{
                            display: true,
                            text: 'Number of Tickets',
                            color: '#94a3b8'
                        }},
                        ticks: {{
                            color: '#e2e8f0'
                        }},
                        grid: {{
                            color: '#334155'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{
                            color: '#e2e8f0',
                            padding: 15,
                            font: {{
                                size: 12
                            }}
                        }}
                    }},
                    title: {{
                        display: true,
                        text: 'Daily Ticket Completion by Project',
                        color: '#fff',
                        font: {{
                            size: 18
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y + ' tickets';
                            }}
                        }}
                    }}
                }},
                onClick: (event, elements) => {{
                    if (elements.length > 0) {{
                        const index = elements[0].index;
                        const date = data.labels[index];
                        const datasets = data.datasets;
                        let total = 0;
                        let details = [];
                        for (let i = 0; i < datasets.length; i++) {{
                            const count = datasets[i].data[index];
                            if (count > 0) {{
                                details.push(datasets[i].label + ': ' + count);
                            }}
                            total += count;
                        }}
                        alert('Date: ' + date + '\\nTotal: ' + total + '\\n' + details.join('\\n'));
                    }}
                }}
            }}
        }};
        
        new Chart(ctx, config);
    </script>
</body>
</html>
"""
    return html

def main():
    print("=" * 60)
    print("QW-002: Tickets-per-day Chart")
    print("=" * 60)
    
    # Load standup data
    print("\n[1/3] Loading standup data...")
    entries = load_standup_data()
    print(f"    Loaded {len(entries)} entries")
    
    # Count tickets per day per project
    print("\n[2/3] Counting tickets per day...")
    daily_counts = count_tickets_per_day(entries)
    
    total_tickets = sum(sum(counts.values()) for counts in daily_counts.values())
    print(f"    Total tickets: {total_tickets}")
    print(f"    Days covered: {len(daily_counts)}")
    
    # Prepare chart data
    print("\n[3/3] Preparing chart data...")
    chart_data = prepare_chart_data(daily_counts)
    
    # Save raw data
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(chart_data, f, indent=2)
    print(f"    Raw data saved to {OUTPUT_JSON}")
    
    # Generate and save HTML
    html = generate_html(chart_data)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"    HTML saved to {OUTPUT_HTML}")
    
    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    print(f"✓ Chart covers {len(chart_data['dates'])} days")
    print(f"✓ {len(chart_data['datasets'])} project datasets")
    print(f"✓ Total tickets: {total_tickets}")
    print("\nQW-002 COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
