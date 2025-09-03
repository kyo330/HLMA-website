from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, Button, Div
from bokeh.layouts import column
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# Sample data (Replace with actual CSV file path)
file_path = '/Users/rpriyadharshini/Desktop/maps/filtered_LYLOUT_230924_210000_0600.csv'
data = pd.read_csv(file_path)

# Adjust the overshooting condition to a realistic threshold
# Setting threshold to 40,000 feet (12,000 meters)
data['is_overshooting'] = data['alt'] > 12000  # Adjust condition to 12 km (12,000 meters)
data['color'] = np.where(data['is_overshooting'], 'red', 'blue')


# Create a ColumnDataSource for Bokeh
source = ColumnDataSource(data)

# Create a Bokeh 2D plot
p2d = figure(title="Lightning Data Visualization - 2D",
             x_axis_label='Longitude', y_axis_label='Latitude',
             tools="lasso_select", width=600, height=400)
p2d.scatter(x='lon', y='lat', source=source, size=10, color='color', alpha=0.6)

# Button to update the 3D plot
button = Button(label="Update 3D Plot", button_type="success")

# Div to display the 3D plot HTML content
plotly_div = Div()

# Function to generate the 3D plot HTML using Plotly
def generate_3d_plot_html(selected_data):
    trace = go.Scatter3d(
        x=selected_data['lon'],
        y=selected_data['lat'],
        z=selected_data['alt'], 
        mode='markers',
        marker=dict(
            size=5,
            color=np.where(selected_data['is_overshooting'], 'red', 'blue')
        )
    )
    fig = go.Figure(data=[trace])
    fig.update_layout(title="Lightning Data Visualization - 3D", width=600, height=400)
    return fig.to_html(include_plotlyjs='cdn')

# Callback to update the 3D plot on button click
def update_3d_plot():
    selected_indices = source.selected.indices
    selected_data = data.iloc[selected_indices]

    if selected_data.empty:
        plotly_div.text = "<p>No data selected. Please select points on the 2D plot.</p>"
    else:
        # Generate the 3D plot HTML and embed it in an iframe
        plotly_html = generate_3d_plot_html(selected_data)
        iframe_html = f"""
            <iframe srcdoc="{plotly_html.replace('"', '&quot;')}" 
                    width="600" height="400" style="border:none;"></iframe>
        """
        plotly_div.text = iframe_html  # Set the iframe HTML in the Div

button.on_click(update_3d_plot)

# Arrange layout
layout = column(p2d, button, plotly_div)

# Add to document
curdoc().add_root(layout)
