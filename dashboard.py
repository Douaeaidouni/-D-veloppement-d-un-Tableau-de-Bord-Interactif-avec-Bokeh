from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Select, WMTSTileSource, ColorBar, LinearColorMapper
from bokeh.layouts import column, row
from bokeh.palettes import Viridis256
from pyproj import Transformer
import pandas as pd
from math import pi
import pandas as pd
from bokeh.models import Div
from bokeh.layouts import column
from bokeh.models import Button
from bokeh.io import export_png
import io

# Créer un titre avec du HTML et du CSS
#title = Div(text="<h1 style='text-align: center; color: #1f77b4;'>Tableau de Bord Interactif avec Bokeh</h1>", width=800)
# Lire le contenu du fichier HTML (qui contient aussi du CSS)
html_content = """
<div style="width: 100%; text-align: center; margin-bottom: 10px;">
    <h1 style="font-size: 2.5em; color: #1f77b4; margin: 0;">Tableau de Bord Interactif avec Bokeh</h1>
</div>
"""
title = Div(text=html_content)



# ------------------------------------------------------------------------
# 1. CHARGEMENT DES DONNÉES
# ------------------------------------------------------------------------

# Charger les données de ventes
sales_df = pd.read_csv('sales_data.csv')
sales_df['date'] = pd.to_datetime(sales_df['date'])
sales_df['day_of_week'] = sales_df['date'].dt.day_name()

# Charger les données géographiques
geo_df = pd.read_csv('geographic_data.csv')
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")
geo_df['x'], geo_df['y'] = transformer.transform(geo_df['latitude'].values, geo_df['longitude'].values)

# Charger les données des feedbacks clients
feedback_df = pd.read_csv('customer_feedback.csv')

# ------------------------------------------------------------------------
# 2. SOURCES DE DONNÉES PARTAGÉES
# ------------------------------------------------------------------------

# Sources initiales
sales_source = ColumnDataSource(sales_df)
geo_source = ColumnDataSource(geo_df)



# Source agrégée pour le graphique en barres
category_source = ColumnDataSource(sales_df.groupby('category')['sales'].sum().reset_index())

# Source agrégée pour la heatmap
heatmap_data = sales_df.groupby(['day_of_week', 'category'])['sales'].sum().reset_index()
heatmap_source = ColumnDataSource(heatmap_data)
avg_rating_source = ColumnDataSource()


# ------------------------------------------------------------------------
# 3. GRAPHIQUES
# ------------------------------------------------------------------------

# 3.1. Tendance des ventes
def create_sales_trend():
    p = figure(title="Tendance des Ventes Quotidiennes", x_axis_type='datetime', height=400, width=600)
    p.line('date', 'sales', line_width=2, color="navy", source=sales_source)
    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = "Ventes (€)"
    hover = HoverTool(tooltips=[("Date", "@date{%F}"), ("Ventes", "@sales{0,0}")], formatters={'@date': 'datetime'})
    p.add_tools(hover)
    return p

# 3.2. Graphique en barres
def create_sales_by_category():
    p = figure(x_range=category_source.data['category'], title="Ventes Totales par Catégorie", height=400, width=600)
    p.vbar(x='category', top='sales', width=0.7, source=category_source, color="blue")
    p.xaxis.axis_label = "Catégorie"
    p.yaxis.axis_label = "Ventes (€)"
    hover = HoverTool(tooltips=[("Catégorie", "@category"), ("Ventes", "@sales{0,0}")])
    p.add_tools(hover)
    return p

# 3.3. Heatmap
def create_sales_heatmap():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    categories = sales_df['category'].unique().tolist()

    mapper = LinearColorMapper(palette=Viridis256, low=heatmap_data['sales'].min(), high=heatmap_data['sales'].max())

    p = figure(title="Carte de Chaleur des Ventes", x_range=categories, y_range=list(reversed(days)),
               height=400, width=600)
    p.rect(x='category', y='day_of_week', width=1, height=1, source=heatmap_source,
           fill_color={'field': 'sales', 'transform': mapper}, line_color=None)

    color_bar = ColorBar(color_mapper=mapper, width=8, location=(0, 0))
    p.add_layout(color_bar, 'right')

    hover = HoverTool(tooltips=[("Jour", "@day_of_week"), ("Catégorie", "@category"), ("Ventes", "@sales{0,0}")])
    p.add_tools(hover)
    return p

# 3.4. Carte géographique
def create_geographic_map():
    tile_url = "http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png"
    tile_source = WMTSTileSource(url=tile_url)

    p = figure(title="Carte des Ventes par Région", x_axis_type="mercator", y_axis_type="mercator",
               height=400, width=600)
    p.add_tile(tile_source)
    p.circle(x='x', y='y', size=15, color="blue", alpha=0.6, source=geo_source)

    hover = HoverTool(tooltips=[("Région", "@region"), ("Ventes", "@sales{0,0}€"), ("Part de Marché", "@market_share{0.0%}")])
    p.add_tools(hover)
    return p

def create_avg_rating_by_category():
    # Calculer la moyenne des notes par catégorie
    avg_ratings = feedback_df.groupby('category')['rating'].mean().reset_index()
    
    # Graphique en barres horizontales
    p = figure(y_range=avg_ratings['category'], title="Note Moyenne par Catégorie",
               height=400, width=600, x_axis_label="Note Moyenne (1-5)", y_axis_label="Catégorie")
    
    p.hbar(y='category', right='rating', height=0.4, source=ColumnDataSource(avg_ratings), color="green")
    
    hover = HoverTool(tooltips=[("Catégorie", "@category"), ("Note Moyenne", "@rating{0.2f}")])
    p.add_tools(hover)
    
    return p

def export_data():
    # Créer un DataFrame à partir des données affichées
    export_df = sales_df.copy()  # Par exemple, exporter les données de ventes
    
    # Enregistrer le DataFrame dans un fichier CSV en mémoire
    csv_data = export_df.to_csv(index=False)
    
    # Créer un fichier binaire avec les données CSV
    csv_bytes = io.BytesIO(csv_data.encode('utf-8'))
    
    # Créer un lien de téléchargement pour l'utilisateur
    import webbrowser
    import os
    from tempfile import NamedTemporaryFile

    # Sauvegarder le fichier CSV temporairement
    with NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
        temp_file.write(csv_bytes.read())
        temp_file.close()
        
        # Ouvrir le fichier CSV dans le navigateur pour téléchargement
        webbrowser.open('file://' + temp_file.name)

# ------------------------------------------------------------------------
# 6.2. Création du bouton d'exportation
# ------------------------------------------------------------------------

export_button = Button(label="Exporter les données", button_type="success")
export_button.on_click(export_data)


# ------------------------------------------------------------------------
# 4. WIDGETS INTERACTIFS
# ------------------------------------------------------------------------

category_filter = Select(title="Catégorie", value="All", options=["All"] + sales_df['category'].unique().tolist())
region_filter = Select(title="Région", value="All", options=["All"] + geo_df['region'].unique().tolist())

def update_data(attr, old, new):
    filtered_sales = sales_df.copy()
    filtered_geo = geo_df.copy()

    # Appliquer les filtres
    if category_filter.value != "All":
        filtered_sales = filtered_sales[filtered_sales['category'] == category_filter.value]
    if region_filter.value != "All":
        filtered_geo = filtered_geo[filtered_geo['region'] == region_filter.value]

    # Mettre à jour les sources principales
    sales_source.data = ColumnDataSource.from_df(filtered_sales)
    geo_source.data = ColumnDataSource.from_df(filtered_geo)

    # Recalculer les données agrégées pour les barres et la heatmap
    updated_category_data = filtered_sales.groupby('category')['sales'].sum().reset_index()
    category_source.data = ColumnDataSource.from_df(updated_category_data)

    updated_heatmap_data = filtered_sales.groupby(['day_of_week', 'category'])['sales'].sum().reset_index()
    heatmap_source.data = ColumnDataSource.from_df(updated_heatmap_data)

category_filter.on_change("value", update_data)
region_filter.on_change("value", update_data)

def update_data(attr, old, new):
    # Filtrer les données en fonction des sélections
    filtered_feedback = feedback_df.copy()
    if category_filter.value != "All":
        filtered_feedback = filtered_feedback[filtered_feedback['category'] == category_filter.value]
    avg_ratings = filtered_feedback.groupby('category')['rating'].mean().reset_index()
    avg_rating_source.data = avg_ratings

# ------------------------------------------------------------------------
# 5. ASSEMBLAGE DU TABLEAU DE BORD
# ------------------------------------------------------------------------

sales_trend = create_sales_trend()
sales_bar = create_sales_by_category()
sales_heatmap = create_sales_heatmap()
geo_map = create_geographic_map()
avg_rating_by_category = create_avg_rating_by_category()



layout = column(title,
    row(export_button),            
    row(category_filter, region_filter),
    row(sales_trend, sales_bar),
    row(sales_heatmap, geo_map),
  
    row(avg_rating_by_category),

    )

    
    

# ------------------------------------------------------------------------
# 6. AFFICHAGE DU TABLEAU DE BORD
# ------------------------------------------------------------------------
curdoc().add_root(layout)
curdoc().title = "Tableau de Bord des Ventes"