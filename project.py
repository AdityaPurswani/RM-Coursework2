import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable



df = pd.read_csv('data.csv')
metrics = ['mean_bio', 'mean_land', 'mean_watuse', 'mean_ghgs', 'mean_eut']
#for metric in metrics:
#    df[metric] = pd.qcut(df[metric], q=100, labels=[i for i in range(1, 101)]).astype(int)
grouped_data = df.groupby(['diet_group', 'age_group', 'sex'])[metrics].mean().reset_index()




supple_agg_df = pd.read_excel('supple_agg_df.xlsx')
supple_agg_df.dropna(inplace=True)
dietary_data_df = pd.read_excel('dietary_data_proportioned.xlsx')
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

def calculate_land_use(selected_diet_category):
    proportions_basedon_dietgroup = dietary_data_df[dietary_data_df['Diet'] == selected_diet_category]
    supple_agg_df['ProportionatedLandUseByDietType'] = supple_agg_df.apply(
        lambda row: row['LandUse(m2*year)'] * (proportions_basedon_dietgroup[row['Category']].values[0]), axis=1
    )
    land_use_summed = supple_agg_df.groupby('Country')['ProportionatedLandUseByDietType'].sum().reset_index()
    return land_use_summed




app = Dash(__name__)


app.layout = html.Div(children=[
    html.Div([
    html.H2("Sunburst Chart", style={'text-align': 'left', 'padding-left': '10px', 'padding-right': '10px'}), 
    dcc.RadioItems(
        id='metric-dropdown',
        options=[{'label': metric, 'value': metric} for metric in metrics],
        value=metrics[0],  # Default value
        inputStyle={'display': 'inline-block', 'margin-right': '10px'},  # Set display style
        labelStyle={'display': 'inline-block', 'margin-right': '10px'},
        style = {'padding-left': '10px', 'padding-right': '10px'}
    ),
    dcc.Graph(id='treemap-chart'),
    ],style={'width': '50%', 'height': '100vh', 'display': 'inline-block', 'vertical-align': 'top', }),

    html.Div([
        html.H2("Country-wise Land use by Diet Type", style={'text-align': 'left', 'padding-left': '10px', 'padding-right': '10px'}), 
                dcc.RadioItems(
                    id='diet-category-dropdown',
                    options=[{'label': diet_category, 'value': diet_category} for diet_category in dietary_data_df['Diet'].unique()],
                    value="Vegans",  inputStyle={'display': 'inline-block', 'margin-right': '10px'},  # Set display style
        labelStyle={'display': 'inline-block', 'margin-right': '10px'},
        style={'padding-left': '10px', 'padding-right': '10px'}
                ),
                dcc.Graph(id='choropleth-chart')
            ], style={'width': '50%', 'height': '100vh', 'display': 'inline-block', 'vertical-align': 'top', })

])

@app.callback(
    Output('treemap-chart', 'figure'),
    [Input('metric-dropdown', 'value')]
)

def update_treemap_chart(selected_metric):
    rdylgn_reversed = [
        "#006837",  # Dark green
        "#31a354",  # Green
        "#78c679",  # Light green
        "#c2e699",  # Yellow-green
        "#ffffbf",  # Yellow
        "#fee08b",  # Light orange
        "#fdae61",  # Orange
        "#f46d43",  # Red-orange
        "#d73027",  # Dark red
        "#a50026"   # Deep red
    ]

    fig = px.sunburst(
        grouped_data,
        path=['diet_group', 'age_group', 'sex'],
        values=selected_metric,
        color = selected_metric,
         color_continuous_scale=rdylgn_reversed,
    )
    fig.update_layout(width=800, height=800)
    return fig


@app.callback(
    Output('choropleth-chart', 'figure'),
    [Input('diet-category-dropdown', 'value')]
)

def update_choropleth(selected_diet_category):
    land_use_summed = calculate_land_use(selected_diet_category)
    # Merge land use data with the GeoDataFrame
    merged_data = world.merge(land_use_summed, left_on='name', right_on='Country', how='left')
    merged_data['ProportionatedLandUseByDietType'].fillna(0, inplace=True)
    choropleth_fig = px.choropleth(
        merged_data,
        locations='iso_a3',
        color='ProportionatedLandUseByDietType',
        hover_name='name',
        color_continuous_scale='RdYlGn_r',
        range_color=(0, 200),
        labels={'ProportionatedLandUseByDietType': ''}
    )
    choropleth_fig.update_layout(
    plot_bgcolor='rgba(0, 0, 0, 0)',
    paper_bgcolor='rgba(0, 0, 0, 0)', margin=dict(t=10, b=10, l=10, r=10)
    )
    return choropleth_fig


# Run the application
if __name__ == '__main__':
    app.run_server(debug=True, port=8000)