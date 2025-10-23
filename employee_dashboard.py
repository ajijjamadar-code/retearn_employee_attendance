import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# === Step 1: Load Excel ===
excel_path = r"C:\attendance\Retearn Emp In & Out details.xlsx"
df = pd.read_excel(excel_path)

# === Step 2: Data cleaning ===
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

# === Step 3: Dash App Setup ===
app = Dash(__name__)

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
        dcc.Graph(id='avg-hours', style={'height': '380px', 'width': '95%', 'margin': 'auto'}),
        html.Br(),
        dcc.Graph(id='avg-in-time', style={'height': '380px', 'width': '95%', 'margin': 'auto'}),
        html.Br(),
        dcc.Graph(id='daily-in-time', style={'height': '380px', 'width': '95%', 'margin': 'auto'}),
        html.Br(),
        dcc.Graph(id='daily-total-hours', style={'height': '380px', 'width': '95%', 'margin': 'auto'})
    ])
], style={'fontFamily': 'Segoe UI, sans-serif', 'backgroundColor': '#FAFAFA', 'padding': '10px 0'})


# === Step 4: Callbacks for Interactive Updates ===
@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('avg-hours', 'figure'),
     Output('avg-in-time', 'figure'),
     Output('daily-in-time', 'figure'),
     Output('daily-total-hours', 'figure')],
    [Input('emp-filter', 'value')]
)
def update_graphs(selected_emp):
    filtered = df.copy()
    if selected_emp:
        filtered = filtered[filtered['Name'] == selected_emp]

    # === Scatter Plot (<8 hrs only) ===
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
        template="plotly_white",
        height=420,
        margin=dict(l=60, r=40, t=60, b=60)
    )

    # === Average Calculations ===
    avg_df = filtered.groupby(['EMP ID', 'Name']).agg(
        Avg_Work_Hours=('Total Hours (hr)', 'mean'),
        Avg_IN_Time=('IN (hr)', 'mean'),
        Days_Worked=('Date', 'count')
    ).reset_index()

    if avg_df.empty:
        return fig1, go.Figure(), go.Figure(), go.Figure(), go.Figure()

    def float_to_time_string(h_float):
        hours = int(h_float)
        minutes = int(round((h_float - hours) * 60))
        t = datetime(2025, 1, 1, hours, minutes)
        return t.strftime("%I:%M %p")

    avg_df['Avg_IN_Display'] = avg_df['Avg_IN_Time'].apply(float_to_time_string)
    avg_df['Avg_IN_Timestamp'] = avg_df['Avg_IN_Time'].apply(lambda h: datetime(2025, 1, 1) + timedelta(hours=h))

    # === Average Working Hours Bar ===
    fig2 = px.bar(
        avg_df,
        x='Name',
        y='Avg_Work_Hours',
        text='Avg_Work_Hours',
        color='Name',
        title='Average Working Hours per Employee',
        template='plotly_white'
    )
    fig2.update_traces(texttemplate='%{text:.2f} hrs', textposition='outside')
    fig2.update_layout(showlegend=False, yaxis_title="Average Hours", height=500,
                       margin=dict(l=60, r=40, t=60, b=60))

    # === Average IN Time Bar ===
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=avg_df['Name'],
        y=avg_df['Avg_IN_Timestamp'],
        text=avg_df['Avg_IN_Display'],
        textposition='outside',
        marker_color=px.colors.qualitative.Set2,
        name='Avg IN Time'
    ))

    fig3.update_layout(
        title="Average IN Time per Employee",
        xaxis_title="Employee",
        yaxis_title="Average IN Time",
        yaxis=dict(tickformat="%I:%M %p", type='date'),
        template="plotly_white",
        height=380,
        showlegend=False,
        margin=dict(l=60, r=40, t=60, b=60)
    )

    # === Daily IN Time (Line Chart) ===
    daily_in_df = filtered.copy()
    daily_in_df['IN_Timestamp'] = daily_in_df['IN (hr)'].apply(lambda h: datetime(2025, 1, 1) + timedelta(hours=h))
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=daily_in_df['Date'],
        y=daily_in_df['IN_Timestamp'],
        mode='lines+markers',
        line=dict(width=3, color='#0074D9'),
        marker=dict(size=8),
        text=daily_in_df['IN'],
        hovertemplate="Date: %{x|%d-%b-%Y}<br>IN Time: %{text}<extra></extra>",
        name='IN Time'
    ))
    fig5.update_layout(
        title="Daily IN Time per Employee (Line Chart)",
        xaxis_title="Date",
        yaxis_title="IN Time",
        yaxis=dict(tickformat="%I:%M %p", type='date'),
        template="plotly_white",
        height=380,
        margin=dict(l=60, r=40, t=60, b=60),
        showlegend=False
    )

    # === Daily Total Hours (Line Chart) ===
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=filtered['Date'],
        y=filtered['Total Hours (hr)'],
        mode='lines+markers',
        line=dict(width=3, color='#FF5733'),
        marker=dict(size=8),
        hovertemplate="Date: %{x|%d-%b-%Y}<br>Total Hours: %{y:.2f}<extra></extra>",
        name='Total Hours'
    ))
    fig4.update_layout(
        title="Total Working Hours per Day (Line Chart)",
        xaxis_title="Date",
        yaxis_title="Total Hours",
        template="plotly_white",
        height=380,
        margin=dict(l=60, r=40, t=60, b=60),
        showlegend=False
    )

    return fig1, fig2, fig3, fig5, fig4


# === Step 5: Run Dashboard ===
if __name__ == "__main__":
    app.run(debug=True)
