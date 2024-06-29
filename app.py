from dotenv import load_dotenv
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from sqlalchemy import create_engine

load_dotenv()

def extraer_datos():
    DATABASE_URL = os.getenv('DATABASE_URL')
    try:
        engine = create_engine(DATABASE_URL)
        query_all = "SELECT * FROM ventas"
        df_all = pd.read_sql(query_all, engine)
        engine.dispose()
        return df_all
    except Exception as e:
        print(f"Error al conectar o extraer los datos: {str(e)}")
        return None

df = extraer_datos()

numeric_columns = ['total', 'cantidad', 'valor_unitario', 'valor_total', 'costo_envio', 'ganancia_neta', 'precio']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df['fecha_compra'] = pd.to_datetime(df['fecha_compra'], errors='coerce')

with open('brazil-states.geojson', 'r', encoding='utf-8') as f: geojson_br = json.load(f)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

color_palette = px.colors.qualitative.Pastel # Definir una paleta de colores personalizada

app = dash.Dash(__name__)
server = app.server
def update_figure_layout(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial", size=12),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return fig

app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand='Dashboard de Ventas - Name: mejorado.py',
        brand_href="#",
        color="primary",
        dark=True,
        className='mb-5'
    ),
    dbc.Row([
        dbc.Col(html.H1("Análisis de Ventas",
                className="text-center mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Ventas Totales", className="card-title"),
                html.H2(f"${df['total'].sum():,.0f}",
                        className="card-text text-primary")
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Productos Vendidos", className="card-title"),
                html.H2(f"{df['cantidad'].sum():,}",
                        className="card-text text-success")
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Ganancia Neta", className="card-title"),
                html.H2(f"${df['ganancia_neta'].sum():,.0f}",
                        className="card-text text-info")
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Clientes Únicos", className="card-title"),
                html.H2(f"{df['producto_id'].nunique():,}",
                        className="card-text text-warning")
            ])
        ]), width=3),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='region-dropdown',
            options=[{'label': 'Seleccionar Todas', 'value': 'ALL'}] +
                [{'label': region, 'value': region}
                    for region in df['name_region'].unique()],
            multi=True,
            placeholder="Seleccionar Región(es)"
                ), width=4),
        dbc.Col(dcc.Dropdown(
            id='marca-dropdown',
            options=[{'label': 'Seleccionar Todas', 'value': 'ALL'}] +
            [{'label': marca, 'value': marca}
                for marca in df['marca'].unique()],
            multi=True,
            placeholder="Seleccionar Marca(s)"
        ), width=4),

        dbc.Col(dcc.DatePickerRange(
            id='date-range',
            start_date=df['fecha_compra'].min(),
            end_date=df['fecha_compra'].max(),
            display_format='YYYY-MM-DD'
        ), width=4),
    ], className="mb-4"),
    dbc.Tabs([
        dbc.Tab(label='Resumen General', tab_id='tab-1'),
        dbc.Tab(label='Análisis de Productos', tab_id='tab-2'),
        dbc.Tab(label='Análisis Geográfico', tab_id='tab-3'),
        dbc.Tab(label='Análisis Temporal', tab_id='tab-4'),
        dbc.Tab(label='Análisis de Vendedores', tab_id='tab-5'),
        dbc.Tab(label='Tendencias de Categorías', tab_id='tab-6'),
        dbc.Tab(label='Demografía del Cliente', tab_id='tab-7'),
        dbc.Tab(label='Análisis de Beneficios', tab_id='tab-8'),
    ], id='tabs', active_tab='tab-1'),
    html.Div(id='tab-content', className='mt-4')
], fluid=True)

tiltes_format = {'text': 'Ventas por Región',
               'x': 0.5,'font': {'size':22, 'color':"RebeccaPurple", 'family': 'Arial black' }}
               # 'font': {'size':22, 'color':"RebeccaPurple", 'family': 'Arial black' }}

@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('region-dropdown', 'value'),
     Input('marca-dropdown', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)

def render_tab_content(active_tab, selected_regions, selected_marcas, start_date, end_date):
    filtered_df = df
    if selected_regions and 'ALL' not in selected_regions:
        filtered_df = filtered_df[filtered_df['name_region'].isin(selected_regions)]
    if selected_marcas and 'ALL' not in selected_marcas:
        filtered_df = filtered_df[filtered_df['marca'].isin(selected_marcas)]
    if start_date and end_date:
        filtered_df = filtered_df[(filtered_df['fecha_compra'] >= start_date) & (filtered_df['fecha_compra'] <= end_date)]

    if active_tab == 'tab-1':
        fig1 = px.pie(filtered_df, names='condicion', values='total',
                      title='Ventas por Condición del Producto', color_discrete_sequence=color_palette)
        fig1.update_layout(title=tiltes_format)
      #   fig1.update_layout(title_pad_b=500,title_pad_t=100,title_x=.2)
        fig1 = update_figure_layout(fig1)

        fig2 = px.bar(filtered_df.groupby('name_region')['total'].sum(
        ).reset_index(), x='name_region', y='total', color='name_region', color_continuous_scale='Blues_r')
        fig2.update_layout(title=tiltes_format)
        fig2.update_xaxes(rangeslider_visible=True)
        fig2 = update_figure_layout(fig2)

        fig3 = px.scatter(filtered_df, x='valor_unitario', y='cantidad', color='marca',
                          size='total', hover_data=['producto'], title='Relación Precio-Cantidad-Total')
        fig3.update_layout(title=tiltes_format)
        fig3 = update_figure_layout(fig3)

        fig4 = px.sunburst(filtered_df, path=['name_region', 'marca', 'producto'],
                           values='total', title='Jerarquía de Ventas por Región, Marca y Producto')
        fig4.update_layout(title=tiltes_format,height=1000)      
        fig4 = update_figure_layout(fig4)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=6),
            dbc.Col(dcc.Graph(figure=fig2), width=6),
            html.Hr(),
            dbc.Col(dcc.Graph(figure=fig3), width=12),
            html.Hr(),
            dbc.Col(dcc.Graph(figure=fig4), width=12),
        ])
    elif active_tab == 'tab-2':
        fig1 = px.treemap(filtered_df, path=[
                          'marca', 'producto'], values='total', title='Jerarquía de Ventas por Marca y Producto')
        fig1 = update_figure_layout(fig1)

        fig2 = px.box(filtered_df, x='marca', y='valor_unitario', title='Distribución de Precios por Marca')
        fig2 = update_figure_layout(fig2)

        fig3 = px.scatter(filtered_df, x='precio', y='ganancia_neta', color='marca', hover_data=[
                          'producto'], title='Relación Precio-Ganancia por Marca')
        fig3 = update_figure_layout(fig3)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=12),
            dbc.Col(dcc.Graph(figure=fig2), width=6),
            dbc.Col(dcc.Graph(figure=fig3), width=6),
        ])
   
    elif active_tab == 'tab-3':
        fig1 = px.choropleth(filtered_df.groupby('abbrev_state')['total'].sum().reset_index(),
                             geojson=geojson_br, locations='abbrev_state',
                             color='total', scope="south america",
                             featureidkey='properties.sigla',
                             title='Ventas Totales por Estado')
        fig1 = update_figure_layout(fig1)

        fig2 = px.bar(filtered_df.groupby('ciudad')['total'].sum().sort_values(ascending=False).head(10).reset_index(),
                      x='ciudad', y='total', title='Top 10 Ciudades por Ventas',color='ciudad')
        fig2.update_xaxes(rangeslider_visible=True)
        fig2 = update_figure_layout(fig2)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=12),
            dbc.Col(dcc.Graph(figure=fig2), width=12),
        ])

    elif active_tab == 'tab-4':
        df_monthly = filtered_df.groupby(filtered_df['fecha_compra'].dt.to_period('M'))[
            'total'].sum().reset_index()
        df_monthly['fecha_compra'] = df_monthly['fecha_compra'].astype(str)

        fig1 = px.line(filtered_df.groupby('fecha_compra')['total'].sum().reset_index(
        ), x='fecha_compra', y='total', title='Tendencia de Ventas en el Tiempo')
        fig1.update_xaxes(rangeslider_visible=True)
        fig1 = update_figure_layout(fig1)

        fig2 = px.bar(df_monthly, x='fecha_compra',
                      y='total', title='Ventas Mensuales')
        fig2.update_xaxes(rangeslider_visible=True)
        fig2 = update_figure_layout(fig2)

        fig3 = px.box(filtered_df, x=filtered_df['fecha_compra'].dt.day_name(
        ), y='total', title='Distribución de Ventas por Día de la Semana')
        fig3 = update_figure_layout(fig3)

        fig4 = px.scatter(filtered_df, x='fecha_compra', y='total', size='cantidad', color='marca', hover_data=[
                          'producto'], title='Evolución de Ventas por Marca en el Tiempo')
        fig4 = update_figure_layout(fig4)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=12),
            dbc.Col(dcc.Graph(figure=fig2), width=6),
            dbc.Col(dcc.Graph(figure=fig3), width=6),
            dbc.Col(dcc.Graph(figure=fig4), width=12),
        ])
    elif active_tab == 'tab-5':
        fig1 = px.bar(filtered_df.groupby('nombre_vendedor')['total'].sum().sort_values(ascending=False).head(10).reset_index(),
                      x='nombre_vendedor', y='total', color='nombre_vendedor', color_continuous_scale='Blues_r', title='Top 10 Vendedores por Ventas Totales')
        fig1.update_xaxes(rangeslider_visible=True)
        fig1 = update_figure_layout(fig1)

        fig2 = px.scatter(filtered_df.groupby('nombre_vendedor').agg({'total': 'sum', 'cantidad': 'sum'}).reset_index(),
                          x='cantidad', y='total', hover_name='nombre_vendedor',
                          title='Relación entre Cantidad Vendida y Total de Ventas por Vendedor')
        fig2 = update_figure_layout(fig2)

        fig3 = px.box(filtered_df, x='nombre_vendedor', y='ganancia_neta',
                      title='Distribución de Ganancias por Vendedor')
        fig3 = update_figure_layout(fig3)

        fig4 = px.scatter(filtered_df.groupby('nombre_vendedor').agg({'total': 'sum', 'ganancia_neta': 'sum'}).reset_index(),
                          x='total', y='ganancia_neta', hover_name='nombre_vendedor',
                          title='Relación entre Ventas Totales y Ganancia Neta por Vendedor')
        fig4 = update_figure_layout(fig4)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=6),
            dbc.Col(dcc.Graph(figure=fig2), width=6),
            dbc.Col(dcc.Graph(figure=fig3), width=12),
            dbc.Col(dcc.Graph(figure=fig4), width=12),
        ])
    elif active_tab == 'tab-6':
        fig1 = px.line(filtered_df.groupby(['product_genero', 'fecha_compra'])['total'].sum().reset_index(),
                       x='fecha_compra', y='total', color='product_genero', title='Tendencias de Ventas por Género del Producto')
        fig1.update_xaxes(rangeslider_visible=True)
        fig1 = update_figure_layout(fig1)

        fig2 = px.bar(filtered_df.groupby('product_genero')['total'].sum().reset_index(),
                      x='product_genero', y='total', title='Ventas Totales por Género del Producto')
        fig2.update_xaxes(rangeslider_visible=True)
        fig2 = update_figure_layout(fig2)

        fig3 = px.box(filtered_df, x='product_genero', y='valor_unitario',
                      title='Distribución de Precios por Género del Producto')
        fig3 = update_figure_layout(fig3)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=12),
            dbc.Col(dcc.Graph(figure=fig2), width=6),
            dbc.Col(dcc.Graph(figure=fig3), width=6),
        ])
    elif active_tab == 'tab-7':
        fig1 = px.histogram(filtered_df, x='name_region',
                            title='Distribución de Ventas por Región')
        fig1 = update_figure_layout(fig1)

        fig2 = px.bar(filtered_df.groupby('product_genero')['total'].sum().reset_index(),
                      x='product_genero', y='total', title='Ventas Totales por Género del Producto')
        fig2.update_xaxes(rangeslider_visible=True)
        fig2 = update_figure_layout(fig2)

        fig3 = px.scatter(filtered_df, x='name_region', y='total', color='product_genero',
                          hover_data=['producto'], title='Relación Región-Ventas por Género del Producto')
        fig3 = update_figure_layout(fig3)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=12),
            dbc.Col(dcc.Graph(figure=fig2), width=6),
            dbc.Col(dcc.Graph(figure=fig3), width=6),
        ])
    elif active_tab == 'tab-8':
        fig1 = px.bar(filtered_df.groupby('nombre_vendedor')['ganancia_neta'].sum().sort_values(ascending=False).head(10).reset_index(),
                      x='nombre_vendedor', y='ganancia_neta', title='Top 10 Vendedores por Ganancia Neta',color='nombre_vendedor')
        fig1.update_xaxes(rangeslider_visible=True)
        fig1 = update_figure_layout(fig1)

        fig2 = px.scatter(filtered_df, x='precio', y='ganancia_neta', color='marca', hover_data=[
                          'producto'], title='Relación Precio-Ganancia Neta por Marca')
        fig2 = update_figure_layout(fig2)

        fig3 = px.box(filtered_df, x='marca', y='ganancia_neta',
                      title='Distribución de Ganancias por Marca')
        fig3 = update_figure_layout(fig3)

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), width=12),
            dbc.Col(dcc.Graph(figure=fig2), width=6),
            dbc.Col(dcc.Graph(figure=fig3), width=6),
        ])

if __name__ == '__main__':
    app.run_server(debug=True)