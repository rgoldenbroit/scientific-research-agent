"""
Plotly chart generation tools for interactive HTML visualizations.
Creates local HTML files that can be opened in any browser.
"""
import os
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px

# Default output directory - relative to project root
DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output"
)


def _ensure_output_dir(output_dir: str = None) -> str:
    """Ensure output directory exists and return absolute path."""
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    return str(output_path)


def _generate_filename(title: str, prefix: str = "chart") -> str:
    """Generate a unique filename from title and timestamp."""
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in title)
    safe_title = safe_title.replace(' ', '_').lower()[:30]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{safe_title}_{timestamp}"


def create_plotly_chart(
    data: dict,
    chart_type: str = "bar",
    title: str = "",
    x_axis_title: str = "",
    y_axis_title: str = "",
    filename: str = None,
    output_dir: str = None,
) -> dict:
    """
    Create an interactive Plotly chart and save as HTML.

    Args:
        data: Dictionary where keys are column headers and values are lists of data.
              Example: {"Category": ["A", "B", "C"], "Value": [10, 20, 30]}
        chart_type: One of: "bar", "horizontal_bar", "line", "pie", "scatter", "grouped_bar"
        title: Chart title
        x_axis_title: X-axis label
        y_axis_title: Y-axis label
        filename: Custom filename (without extension)
        output_dir: Output directory path

    Returns:
        dict with status, file_path, filename, message
    """
    try:
        if not data or not isinstance(data, dict):
            return {
                "status": "error",
                "message": "Data must be a non-empty dictionary with column headers as keys."
            }

        headers = list(data.keys())
        if len(headers) < 2:
            return {
                "status": "error",
                "message": "Data must have at least 2 columns (x and y values)."
            }

        output_path = _ensure_output_dir(output_dir)

        if filename is None:
            filename = _generate_filename(title or "chart", "chart")

        fig = None
        x_col = headers[0]
        y_cols = headers[1:]

        if chart_type == "bar":
            fig = go.Figure()
            for y_col in y_cols:
                fig.add_trace(go.Bar(x=data[x_col], y=data[y_col], name=y_col))

        elif chart_type == "horizontal_bar":
            fig = go.Figure()
            for y_col in y_cols:
                fig.add_trace(go.Bar(x=data[y_col], y=data[x_col],
                                     name=y_col, orientation='h'))

        elif chart_type == "line":
            fig = go.Figure()
            for y_col in y_cols:
                fig.add_trace(go.Scatter(x=data[x_col], y=data[y_col],
                                         mode='lines+markers', name=y_col))

        elif chart_type == "pie":
            fig = go.Figure(data=[go.Pie(labels=data[x_col], values=data[y_cols[0]])])

        elif chart_type == "scatter":
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data[x_col], y=data[y_cols[0]],
                                     mode='markers', name=y_cols[0]))

        elif chart_type == "grouped_bar":
            fig = go.Figure()
            for y_col in y_cols:
                fig.add_trace(go.Bar(x=data[x_col], y=data[y_col], name=y_col))
            fig.update_layout(barmode='group')

        else:
            return {
                "status": "error",
                "message": f"Unknown chart type: {chart_type}. Use: bar, horizontal_bar, line, pie, scatter, grouped_bar"
            }

        fig.update_layout(
            title=dict(text=title, font=dict(size=20)),
            xaxis_title=x_axis_title or x_col,
            yaxis_title=y_axis_title or (y_cols[0] if y_cols else ""),
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=60, r=40, t=80, b=60),
        )

        file_path = os.path.join(output_path, f"{filename}.html")
        fig.write_html(
            file_path,
            full_html=True,
            include_plotlyjs=True,
            config={'displayModeBar': True, 'responsive': True}
        )

        return {
            "status": "success",
            "file_path": file_path,
            "filename": f"{filename}.html",
            "chart_type": chart_type,
            "message": f"Created {chart_type} chart: {file_path}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create chart: {str(e)}"
        }


def create_kaplan_meier_chart(
    survival_data: dict,
    title: str = "Survival Analysis",
    x_axis_title: str = "Time (days)",
    y_axis_title: str = "Survival Probability",
    filename: str = None,
    output_dir: str = None,
) -> dict:
    """
    Create a Kaplan-Meier survival curve plot.

    Args:
        survival_data: Dictionary with group names as keys, each containing:
            {
                "Group Name": {
                    "times": [0, 30, 60, 90, ...],
                    "survival_probs": [1.0, 0.95, 0.90, 0.85, ...],
                }
            }
        title: Chart title
        x_axis_title: X-axis label
        y_axis_title: Y-axis label
        filename: Custom filename
        output_dir: Output directory

    Returns:
        dict with status, file_path, filename, message
    """
    try:
        if not survival_data:
            return {"status": "error", "message": "No survival data provided"}

        output_path = _ensure_output_dir(output_dir)

        if filename is None:
            filename = _generate_filename(title, "km_curve")

        fig = go.Figure()
        colors = px.colors.qualitative.Set1

        for i, (group_name, group_data) in enumerate(survival_data.items()):
            times = group_data.get("times", [])
            probs = group_data.get("survival_probs", [])

            if not times or not probs:
                continue

            color = colors[i % len(colors)]

            fig.add_trace(go.Scatter(
                x=times,
                y=probs,
                mode='lines',
                name=group_name,
                line=dict(shape='hv', color=color, width=2),
                hovertemplate=f"{group_name}<br>Time: %{{x}}<br>Survival: %{{y:.1%}}<extra></extra>"
            ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=20)),
            xaxis_title=x_axis_title,
            yaxis_title=y_axis_title,
            yaxis=dict(range=[0, 1.05], tickformat='.0%'),
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=60, r=40, t=80, b=60),
            hovermode='x unified'
        )

        file_path = os.path.join(output_path, f"{filename}.html")
        fig.write_html(file_path, full_html=True, include_plotlyjs=True)

        return {
            "status": "success",
            "file_path": file_path,
            "filename": f"{filename}.html",
            "chart_type": "kaplan_meier",
            "message": f"Created Kaplan-Meier survival chart: {file_path}"
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to create K-M chart: {str(e)}"}


def create_html_report(
    title: str,
    sections: list,
    chart_files: list = None,
    filename: str = None,
    output_dir: str = None,
) -> dict:
    """
    Create a standalone HTML report with embedded charts.

    Args:
        title: Report title
        sections: List of section dicts:
            [
                {"heading": "Section Title", "content": "HTML/Markdown content"},
                {"heading": "Results", "content": "...", "chart_file": "/path/to/chart.html"},
            ]
        chart_files: Additional chart files to embed at the end
        filename: Custom filename
        output_dir: Output directory

    Returns:
        dict with status, file_path, filename, message
    """
    try:
        output_path = _ensure_output_dir(output_dir)

        if filename is None:
            filename = _generate_filename(title, "report")

        css = """
        <style>
            body {
                font-family: 'Georgia', 'Times New Roman', serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 40px;
                line-height: 1.6;
                color: #333;
                background: #fff;
            }
            h1 {
                color: #1a1a1a;
                border-bottom: 2px solid #333;
                padding-bottom: 10px;
                font-size: 28px;
            }
            h2 {
                color: #2c3e50;
                margin-top: 30px;
                font-size: 22px;
            }
            h3 {
                color: #34495e;
                font-size: 18px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #f5f5f5;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #fafafa;
            }
            .chart-container {
                margin: 30px 0;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
            }
            .chart-container iframe {
                width: 100%;
                height: 500px;
                border: none;
            }
            .metadata {
                color: #666;
                font-size: 14px;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }
            @media print {
                body { padding: 20px; }
                .chart-container iframe { height: 400px; }
            }
        </style>
        """

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{title}</title>",
            css,
            "</head>",
            "<body>",
            f"<h1>{title}</h1>",
        ]

        for section in sections:
            heading = section.get("heading", "")
            content = section.get("content", "")
            chart_file = section.get("chart_file", "")

            if heading:
                html_parts.append(f"<h2>{heading}</h2>")

            if content:
                content = content.replace("\n\n", "</p><p>")
                html_parts.append(f"<p>{content}</p>")

            if chart_file and os.path.exists(chart_file):
                chart_filename = os.path.basename(chart_file)
                html_parts.append(f"""
                <div class="chart-container">
                    <iframe src="{chart_filename}" title="Chart"></iframe>
                </div>
                """)

        if chart_files:
            html_parts.append("<h2>Visualizations</h2>")
            for chart_file in chart_files:
                if os.path.exists(chart_file):
                    chart_filename = os.path.basename(chart_file)
                    html_parts.append(f"""
                    <div class="chart-container">
                        <iframe src="{chart_filename}" title="Chart"></iframe>
                    </div>
                    """)

        html_parts.append(f"""
        <div class="metadata">
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Scientific Research Agent - Interactive Report</p>
        </div>
        """)

        html_parts.extend(["</body>", "</html>"])

        file_path = os.path.join(output_path, f"{filename}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(html_parts))

        return {
            "status": "success",
            "file_path": file_path,
            "filename": f"{filename}.html",
            "sections_count": len(sections),
            "message": f"Created HTML report: {file_path}"
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to create report: {str(e)}"}


def list_output_files(output_dir: str = None) -> dict:
    """
    List all generated output files in the output directory.

    Returns:
        dict with status, files list, directory path
    """
    try:
        output_path = _ensure_output_dir(output_dir)

        files = []
        for f in Path(output_path).glob("*.html"):
            stat = f.stat()
            files.append({
                "filename": f.name,
                "path": str(f),
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        files.sort(key=lambda x: x["modified"], reverse=True)

        return {
            "status": "success",
            "output_dir": output_path,
            "file_count": len(files),
            "files": files
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to list files: {str(e)}"}
