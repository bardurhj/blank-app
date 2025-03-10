import streamlit as st
import requests
import pandas as pd
import json
import pydeck as pdk
import numpy as np

st.title("Jarðhitahol í Føroyum")
st.write(
    "Hetta er eitt grafiskt yvirlit yvir jarðhitahol í Føroyum, sambært almennum skrásetingum hjá Umhvørvisstovuni "
)

# Fetch and display geographical data from Faroe Islands API
# st.subheader("📍 Faroe Islands Addresses Map")

# Construct the API URL - changing format to JSON
# api_url = "https://gis.us.fo/arcgis/rest/services/adressur/us_adr_husanr/MapServer/0/query"
# params = {
#     "where": "1=1",
#     "outFields": "*",
#     "returnGeometry": "true",
#     "f": "geojson"  # Request GeoJSON format
# }

# # Add a loading message
# with st.spinner("Fetching geographical data..."):
#     try:
#         # Make API request
#         response = requests.get(api_url, params=params)
#         response.raise_for_status()  # Raise exception for HTTP errors
        
#         # Parse the response
#         data = response.json()
        
#         # Display map if we have features
#         if 'features' in data and len(data['features']) > 0:
#             # Create a dataframe for the points
            
#             points = []
            
#             for feature in data['features'][:100]:  # Limit to 100 points for performance
#                 if feature['geometry']['type'] == 'Point':
#                     coords = feature['geometry']['coordinates']
#                     # GeoJSON is [longitude, latitude]
#                     points.append({
#                         'lat': coords[1], 
#                         'lon': coords[0],
#                         'address': feature['properties'].get('HUSANR', 'Unknown')
#                     })
            
#             if points:
#                 df = pd.DataFrame(points)
#                 st.map(df)
#                 st.caption(f"Displaying {len(points)} addresses in the Faroe Islands")
#         else:
#             st.error("No geographical features found in the API response")
            
#     except requests.RequestException as e:
#         st.error(f"Error fetching data from API: {e}")
        
#     except Exception as e:
#         st.error(f"Error processing data: {e}")

# # Add a data explorer section
# if 'data' in locals():
#     with st.expander("Explore Raw Data"):
#         st.json(data)

# Add a separator
# st.markdown("---")

# Green Energy Drilled Holes Map Section
st.subheader("🔋 Jarðhitahol")
st.write("Kortið vísir staðseting og aðrar upplýsingar um jarðhitahol í Føroyum.")

# Construct the API URL for green energy drilled holes
green_energy_url = "https://gis.us.fo/arcgis/rest/services/gron_orka/us_jardhiti/MapServer/1/query"
green_energy_params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "json"  # Request JSON format
}

# Add a loading message
with st.spinner("Innlesur data frá Umhvørvisstovuni..."):
    try:
        # Make API request
        response = requests.get(green_energy_url, green_energy_params)
        response.raise_for_status()
        
        # Parse the response
        drill_data = response.json()
        
        if 'features' in drill_data and len(drill_data['features']) > 0:
            # Create a dataframe for the drill points
            drill_points = []
            
            for feature in drill_data['features']:
                if 'geometry' in feature and 'attributes' in feature:
                    attrs = feature['attributes']
                    
                    # Extract coordinates from the geometry
                    # First check if we have points data in the expected format
                    coords = None
                    if 'geometry' in feature:
                        geom = feature['geometry']
                        if 'points' in geom and geom['points'] and len(geom['points']) > 0:
                            # Using the first point if multiple exist
                            point = geom['points'][0]
                            if len(point) >= 2:
                                # These appear to be in a local projection, not lat/lon
                                x, y = point[0], point[1]
                                # Use the lat/lon from attributes instead
                                lat = attrs.get('latitude_geo')
                                lon = attrs.get('longitude_geo')
                                
                                if lat is not None and lon is not None:
                                    # Extract key information from attributes
                                    address = attrs.get('address', 'Unknown')
                                    city = attrs.get('city', '')
                                    length = attrs.get('length', 0)  # Depth of the hole
                                    active_length = attrs.get('active_length', 0)
                                    water_amount = attrs.get('water_amount', 0)
                                    water_temp = attrs.get('water_temperature')
                                    depth_temp = attrs.get('depth_temperature')
                                    groundwater_level = attrs.get('groundwater_level')
                                    drill_date = attrs.get('drill_date')
                                    num_holes = attrs.get('number_of_holes', 1)
                                    effect_needed = attrs.get('effect_needed')
                                    energy_needed = attrs.get('energy_needed')
                                    heated_area = attrs.get('heated_area')
                                    
                                    # Format the drill date if it exists
                                    drill_date_str = ''
                                    if drill_date:
                                        try:
                                            # Convert from timestamp (milliseconds) to datetime
                                            from datetime import datetime
                                            drill_date_obj = datetime.fromtimestamp(drill_date/1000.0)
                                            drill_date_str = drill_date_obj.strftime('%Y-%m-%d')
                                        except:
                                            drill_date_str = str(drill_date)
                                    
                                    drill_points.append({
                                        'lat': lat,
                                        'lon': lon,
                                        'depth': length,  # Using length as depth
                                        'active_depth': active_length,
                                        'name': f"{address}, {city}".strip(", "),
                                        'water_amount': water_amount,
                                        'water_temp': water_temp if water_temp else 'N/A',
                                        'depth_temp': depth_temp if depth_temp else 'N/A',
                                        'groundwater_level': groundwater_level if groundwater_level else 'N/A',
                                        'drill_date': drill_date_str,
                                        'num_holes': num_holes,
                                        'effect_needed': effect_needed,
                                        'energy_needed': energy_needed,
                                        'heated_area': heated_area
                                    })
            
            if drill_points:
                df_drills = pd.DataFrame(drill_points)
                
                # Add visualization options
                viz_type = st.radio(
                    "Vel kortslag:",
                    ["Vanligt kort", "3D Kolonnu kort", "Smálutir"]
                )
                
                if viz_type == "Vanligt kort":
                    # Set view state centered on the Faroe Islands
                    view_state = pdk.ViewState(
                        latitude=62.0,       # Faroe Islands latitude
                        longitude=-7.0,      # Faroe Islands longitude
                        zoom=9,              # Adjusted zoom level for better overview
                        pitch=0
                    )
                    
                    # Create a ScatterplotLayer with smaller points
                    scatter_layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=df_drills,
                        get_position=["lon", "lat"],
                        get_radius=30,  # Smaller radius in meters
                        get_fill_color=[0, 128, 255, 200],  # Blue with some transparency
                        pickable=True,
                        auto_highlight=True
                    )
                    
                    # Create tooltip for interaction
                    tooltip = {
                        "html": "<b>Location:</b> {name}<br>" +
                               "<b>Depth:</b> {depth} m<br>" +
                               "<b>Water amount:</b> {water_amount} l/s<br>" +
                               "<b>Drill date:</b> {drill_date}",
                        "style": {
                            "backgroundColor": "steelblue",
                            "color": "white"
                        }
                    }
                    
                    # Create and display the map
                    r = pdk.Deck(
                        layers=[scatter_layer],
                        initial_view_state=view_state,
                        tooltip=tooltip,
                        map_style="light"
                    )
                    
                    st.pydeck_chart(r)
                    st.caption("Click on any point to see depth information")
                    
                elif viz_type == "3D Kolonnu kort":
                    # First, handle any NaN values in depth
                    df_drills['depth'] = df_drills['depth'].fillna(0)
                    
                    # Normalize depth for visualization
                    max_depth = df_drills['depth'].max()
                    if max_depth > 0:
                        df_drills['elevation'] = df_drills['depth'] / max_depth * 1000
                    else:
                        df_drills['elevation'] = 100  # Default height if no depth data
                    
                    # Create color based on depth - safely handle NaN values
                    if max_depth > 0:
                        # Calculate color values and handle any potential NaN values
                        depth_ratio = df_drills['depth'] / max_depth
                        depth_ratio = depth_ratio.fillna(0)  # Replace any remaining NaNs with 0
                        
                        df_drills['color_r'] = (depth_ratio * 255).astype(int)
                        df_drills['color_g'] = 100
                        df_drills['color_b'] = (255 - df_drills['color_r']).astype(int)
                    else:
                        # Default colors if we can't calculate based on depth
                        df_drills['color_r'] = 0
                        df_drills['color_g'] = 100
                        df_drills['color_b'] = 255
                    
                    # Create a PyDeck map with smaller columns
                    view_state = pdk.ViewState(
                        latitude=62.0,       # Faroe Islands latitude
                        longitude=-7.0,      # Faroe Islands longitude
                        zoom=9,              # Adjusted zoom level for better overview
                        pitch=45
                    )
                    
                    column_layer = pdk.Layer(
                        "ColumnLayer",
                        data=df_drills,
                        get_position=["lon", "lat"],
                        get_elevation="elevation",
                        elevation_scale=1,
                        radius=50,  # Reduced radius size from 100 to 50
                        get_fill_color=["color_r", "color_g", "color_b", 200],
                        pickable=True,
                        auto_highlight=True
                    )
                    
                    tooltip = {
                        "html": "<b>Location:</b> {name}<br>" +
                               "<b>Depth:</b> {depth} m<br>" +
                               "<b>Active depth:</b> {active_depth} m<br>" +
                               "<b>Water amount:</b> {water_amount} l/s<br>" +
                               "<b>Drill date:</b> {drill_date}<br>" +
                               "<b>Number of holes:</b> {num_holes}",
                        "style": {
                            "backgroundColor": "steelblue",
                            "color": "white"
                        }
                    }
                    
                    r = pdk.Deck(
                        layers=[column_layer],
                        initial_view_state=view_state,
                        tooltip=tooltip,
                        map_style="light"
                    )
                    
                    st.pydeck_chart(r)
                    
                    # Add a legend and instructions
                    st.caption("Color represents depth: Blue (shallow) to Red (deep)")
                    st.caption("Click on any column to see detailed information")
                    
                else:  # Detailed Information
                    # Show the most interesting fields in the dataframe
                    display_columns = [
                        'name', 'depth', 'active_depth', 'water_amount', 
                        'water_temp', 'depth_temp', 'groundwater_level',
                        'drill_date', 'num_holes', 'effect_needed', 
                        'energy_needed', 'heated_area', 'lat', 'lon'
                    ]
                    # Only show columns that exist in the dataframe
                    valid_columns = [col for col in display_columns if col in df_drills.columns]
                    st.dataframe(df_drills[valid_columns])
                
                st.caption(f"Displaying {len(drill_points)} drill holes for green energy projects")
                
                # Add drill depth statistics
                if 'depth' in df_drills.columns:
                    # Fill NaN values with 0 for calculations
                    depth_data = df_drills['depth'].fillna(0)
                    
                    st.subheader("Hagtøl fyri jarðhitahol")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Miðal dýpd (m)", f"{depth_data.mean():.1f}")
                    with col2:
                        st.metric("Mesta dýpd (m)", f"{depth_data.max():.1f}")
                    with col3:
                        # This shows the total drill sites/locations
                        st.metric("Tal av støðum", f"{len(df_drills)}")
                    with col4:
                        # This shows the sum of all holes across all locations
                        st.metric("Tal av holum tilsamans", f"{df_drills['num_holes'].fillna(1).sum():.0f}")
                    
                    # Add another row of metrics for more insights
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Miðal hol pr. stað", f"{df_drills['num_holes'].fillna(1).mean():.1f}")
                    with col2:
                        st.metric("Mesta tal av holum á einum stað", f"{df_drills['num_holes'].fillna(1).max():.0f}")
                    with col3:
                        # Calculate total drilled depth (depth * number of holes at each site)
                        total_drilled = (depth_data * df_drills['num_holes'].fillna(1)).sum()
                        st.metric("Borað tilsamans (m)", f"{total_drilled:.1f}")
                    with col4:
                        # Average depth per hole (not per site)
                        if df_drills['num_holes'].fillna(1).sum() > 0:
                            avg_per_hole = total_drilled / df_drills['num_holes'].fillna(1).sum()
                            st.metric("Miðal dýpd pr. hol (m)", f"{avg_per_hole:.1f}")
                    
                    # Add a histogram of depths - ensure we have valid data
                    if len(depth_data) > 0 and not depth_data.isna().all():
                        st.subheader("Depth Distribution")
                        hist_values = np.histogram(depth_data, bins=10)[0]
                        st.bar_chart(hist_values)
                    
                    # If we have both water amount and depth, create a scatter plot
                    if 'water_amount' in df_drills.columns and df_drills['water_amount'].notna().any():
                        st.subheader("Depth vs. Water Amount")
                        chart_data = df_drills[['depth', 'water_amount']].dropna()
                        st.scatter_chart(chart_data, x='depth', y='water_amount')
                    
            else:
                st.error("Could not extract valid drill hole data from the API response")
                
        else:
            st.error("No drill hole features found in the API response")
            
    except requests.RequestException as e:
        st.error(f"Error fetching drill data from API: {e}")
        
    except Exception as e:
        st.error(f"Error processing drill data: {e}")
        st.exception(e)

    # Add raw data explorer
    if 'drill_data' in locals():
        with st.expander("Explore Raw Drill Data"):
            st.json(drill_data)


