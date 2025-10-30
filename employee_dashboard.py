import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# === Step 1: Load Excel File ===
excel_path = r"C:\attendance\data\Retearn Emp In & Out details.xlsx"
df = pd.read_excel(excel_path)

# === Step 2: Data Cleaning ===
def convert_time_to_hours(t):
    try:
        if pd.isna(t):
            return 0
        h, m = map(int, str(t).strip().split(':'))
        return h + m / 60
    except:
        return 0

def convert_in_to_float(t):
    try:
        if pd.isna(t):
            return 0
        h, m = map(int, str(t).split(':'))
        return h + m / 60
    except:
        return 0

df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
df['Total Hours (hr)'] = df['Total Hrs'].apply(convert_time_to_hours)
df['IN (hr)'] = df['IN'].apply(convert_in_to_float)
df['OUT (hr)'] = df['OUT'].apply(convert_in_to_float)

# === Step 3: Dash App Setup ===
app = Dash(__name__)
app.title = "Employee Attendance Dashboard"

app.layout = html.Div([
    html.H2("Employee Attendance Dashboard", style={'textAlign': 'center', 'marginBottom': 20}),

    html.Div([
        html.Label("Select Employee:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='emp-filter',
            options=[{'label': emp, 'value': emp} for emp in sorted(df['Name'].unique())],
            value=None,
            placeholder="Select an Employee",
            clearable=True,
            style={'width': '50%', 'margin': '0 auto'}
        )
    ], style={'textAlign': 'center', 'marginBottom': 30}),

    html.Div([
        dcc.Graph(id='scatter-plot', style={'height': '420px', 'width': '95%', 'margin': 'auto'}),
        html.Br(),
        dcc.Graph(id='in-out-time', style={'height': '380px', 'width': '95%', 'margin': 'auto'}),
        html.Br(),
        dcc.Graph(id='daily-total-hours', style={'height': '380px', 'width': '95%', 'margin': 'auto'})
    ])
], style={'fontFamily': 'Segoe UI, sans-serif', 'backgroundColor': '#FAFAFA', 'padding': '10px 0'})

# === Step 4: Callbacks ===
@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('in-out-time', 'figure'),
     Output('daily-total-hours', 'figure')],
    [Input('emp-filter', 'value')]
)
def update_graphs(selected_emp):
    filtered = df.copy()
    if selected_emp:
        filtered = filtered[filtered['Name'] == selected_emp]

    # === Scatter Plot (<8 hrs) ===
    scatter_df = filtered[filtered['Total Hours (hr)'] < 8]
    color_map = px.colors.qualitative.Plotly
    employees = scatter_df['Name'].unique()
    color_dict = {emp: color_map[i % len(color_map)] for i, emp in enumerate(employees)}

    fig1 = go.Figure()
    for emp in employees:
        temp = scatter_df[scatter_df['Name'] == emp]
        fig1.add_trace(go.Scatter(
            x=temp['Date'],
            y=temp['Total Hours (hr)'],
            mode='markers',
            name=emp,
            marker=dict(size=9, color=color_dict[emp], line=dict(width=1, color='black')),
            customdata=temp[['IN', 'OUT']],
            hovertemplate=(
                "Employee: %{text}<br>"
                "Date: %{x|%d-%b-%Y}<br>"
                "IN: %{customdata[0]}<br>"
                "OUT: %{customdata[1]}<br>"
                "Total: %{y:.2f} hrs<extra></extra>"
            ),
            text=[emp]*len(temp)
        ))
    fig1.update_layout(
        title="Employees Working Less than 8 Hours (Scatter)",
        xaxis_title="Date",
        yaxis_title="Total Hours Worked",
        template="plotly_white"
    )

    # === IN & OUT Time (Line Graph) ===
    filtered['IN_Timestamp'] = filtered['IN (hr)'].apply(lambda h: datetime(2025, 1, 1) + timedelta(hours=h))
    filtered['OUT_Timestamp'] = filtered['OUT (hr)'].apply(lambda h: datetime(2025, 1, 1) + timedelta(hours=h))

    fig_in_out = go.Figure()
    fig_in_out.add_trace(go.Scatter(
        x=filtered['Date'],
        y=filtered['IN_Timestamp'],
        mode='lines+markers',
        name='IN Time',
        line=dict(width=3, color='#2E86C1'),
        marker=dict(size=8),
        hovertemplate="Date: %{x|%d-%b-%Y}<br>IN: %{y|%I:%M %p}<extra></extra>"
    ))

    fig_in_out.add_trace(go.Scatter(
        x=filtered['Date'],
        y=filtered['OUT_Timestamp'],
        mode='lines+markers',
        name='OUT Time',
        line=dict(width=3, color='#E74C3C'),
        marker=dict(size=8),
        hovertemplate="Date: %{x|%d-%b-%Y}<br>OUT: %{y|%I:%M %p}<extra></extra>"
    ))

    fig_in_out.update_layout(
        title="Employee IN and OUT Times (Daily Trend)",
        xaxis_title="Date",
        yaxis_title="Time of Day",
        yaxis=dict(tickformat="%I:%M %p", type='date'),
        template="plotly_white"
    )

    # === Daily Total Hours ===
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=filtered['Date'],
        y=filtered['Total Hours (hr)'],
        mode='lines+markers',
        line=dict(width=3, color='#FF5733'),
        hovertemplate="Date: %{x|%d-%b-%Y}<br>Total Hours: %{y:.2f}<extra></extra>"
    ))
    fig4.update_layout(
        title="Total Working Hours per Day",
        xaxis_title="Date",
        yaxis_title="Total Hours",
        template="plotly_white"
    )

    return fig1, fig_in_out, fig4


# === Step 5: Run Locally ===
if __name__ == "__main__":
    app.run(debug=True)

