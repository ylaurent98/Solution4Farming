import streamlit as st
import plotly.express as px
import sqlite3
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from scipy.stats import gaussian_kde
from selenium import webdriver as wd
import pdfkit
from weasyprint import HTML
import io
import weasyprint
import requests




# st.set_page_config(page_title='Emissions_Dashboard',layout='wide', initial_sidebar_state='expanded')

def get_average_emissions_from_other_users_b ():
    conn = sqlite3.connect('S4F_database.db')
    cursor = conn.cursor()
    cursor.execute("""
    WITH TotalCalc AS (
        SELECT
            user,
            date,
            Enteric_ferm_total + Mannure_management_total + N2O_direct_total + N2O_loss_total + N2O_leaching_total AS TotalValue
        FROM Submissions
        WHERE user != ? AND date >= date('now', '-1 year')
    )
    SELECT AVG(TotalValue) AS AverageTotal
    FROM TotalCalc;
    """, (st.session_state['username'],))

    # Fetch the result
    average_total = cursor.fetchone()[0]
    st.write(f"Average Total: {average_total}")

    # Close the connection
    conn.close()
    return average_total

def dashboard_b():
    labels=['Enteric fermentation', 'Manure management','N₂O direct emissions from manure management', 'N₂O loss through volatilisation following manure management','N₂O loss by leaching following manure management']
    values=[st.session_state['Emission totals']['Enteric_ferm_total'], st.session_state['Emission totals']['Mannure_management_total'], st.session_state['Emission totals']['N2O_direct_total'],st.session_state['Emission totals']['N2O_loss_total'],st.session_state['Emission totals']['N2O_leaching_total']]
        # Create pie chart
    fig = px.pie(names=labels, values=values, title='Greenhouse Gas Emissions')
    st.title("Emission breakdown by source for all livestock categories")
    st.plotly_chart(fig)

def highlight_last_row(s):
    """
    Highlight the last row with a light blue background.
    Highlight the "Total emission" cell of the last row.
    """
    # Use a lighter shade of blue for the last row
    last_row_color = 'background-color: #AFEEEE'

    # Use a darker shade of blue for the "Total emission" cell of the last row
    last_cell_color = 'background-color: #ADD8E6'

    # Default color for all other cells
    default_color = ''

    # Create an empty DataFrame with the same index and columns as the input Series/DataFrame
    styles = pd.DataFrame(default_color, index=s.index, columns=s.columns)

    # Apply the lighter shade of blue to the entire last row
    styles.iloc[-1] = last_row_color

    # Apply the darker shade of blue to the "Total emission" cell of the last row
    styles['Total emissions/category (CO₂eq T/year)'].iloc[-1] = last_cell_color

    return styles

# Function to convert multiple DataFrames to Excel and return as bytes
def convert_dfs_to_excel(_dfs, sheet_names):
    from io import BytesIO

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')

    for df, sheet_name in zip(_dfs, sheet_names):
        df.to_excel(writer, index=False, sheet_name=sheet_name)

    writer.close()
    processed_data = output.getvalue()
    return processed_data




def show_previous_submissions():
    conn = sqlite3.connect('S4F_database.db')
    cursor = conn.cursor()

    # Fetch all submissions
    cursor.execute("SELECT * FROM Submissions WHERE user = ?", (st.session_state['username'],))
    submissions = cursor.fetchall()
    submission_columns = [desc[0] for desc in cursor.description]

    # Rename columns for Submissions
    renamed_submission_columns = {
        "id": "ID",
        "date": "Date",
        "time": "Time",
        "user": "User",
        "FSN": "Synthetic Fertilizers Applied on Field (kg/yr)",
        "FON": "Organic Fertilizers Applied on Ground (kg/yr)",
        "FCR": "Nitrogen from Crop Residues (kg/yr)",
        "FSOM": "Nitrogen Mineralized as Result of Land Use Change(kg/yr)",
        "Electric": "Electricity (MWh/year)",
        "Gas": "Natural gas (m³)",
        "Gasoline": "Gasoline (L)",
        "Biogas": "Biogas (m³)",
        "Water": "Water (m³)",
        "Waste": "Waste (m³)",
        "soil_N2O_direct": "Direct N₂O Emissions from Soil (kg/year)",
        "soil_N2O_indirect": "Indirect N₂O Emissions from Soil (kg/year)",
        "Diesel": "Diesel (L)"
        # Add more renames for Submissions columns as necessary
    }

    # Loop through each submission
    i=0
    show_CO2e= st.checkbox ("Display output data in CO₂ equivalents (tonnes)")
    for submission in submissions:
        # Display submission data in the submission header
        i=i+1
        submission_data = [submission]
        df_submission = pd.DataFrame(submission_data, columns=submission_columns)
        df_submission = df_submission.rename(columns=renamed_submission_columns)
        df_submission_input = df_submission.drop(columns= [ "ID","Date","Time","User","Direct N₂O Emissions from Soil (kg/year)","Indirect N₂O Emissions from Soil (kg/year)"])
        df_submission_output_energy= df_submission.drop(columns= ["ID","Date","Time","User","Synthetic Fertilizers Applied on Field (kg/yr)","Organic Fertilizers Applied on Ground (kg/yr)","Nitrogen from Crop Residues (kg/yr)","Nitrogen Mineralized as Result of Land Use Change(kg/yr)","Water (m³)","Waste (m³)","Direct N₂O Emissions from Soil (kg/year)","Indirect N₂O Emissions from Soil (kg/year)"])
        df_submissions_output_soil= df_submission[['Direct N₂O Emissions from Soil (kg/year)', 'Indirect N₂O Emissions from Soil (kg/year)']]
        df_submissions_output_soil['Total']=df_submissions_output_soil['Direct N₂O Emissions from Soil (kg/year)']+df_submissions_output_soil['Indirect N₂O Emissions from Soil (kg/year)']
        with st.expander(f"# {i}. Sumission ID: {int(df_submission['ID'])} from {str(df_submission['Time'])[2:25]}"):
        #st.markdown(f"# {i}. Sumission ID: {int(df_submission['ID'])} from {str(df_submission['Time'])[2:25]}")
        # Fetch corresponding entries
            cursor.execute("SELECT * FROM Entries WHERE submission_id=?", (submission[0],))
            entries = cursor.fetchall()
            entry_columns = [desc[0] for desc in cursor.description]

            # Reorder and rename columns for Entries
            desired_order = ['id', 'Livestock_category'] + [col for col in entry_columns if col not in ['id', 'Livestock_category']]
            renamed_entry_columns = {

                "id": "ID",
                "Livestock_category": "Livestock Category",
                "paie_orz": "Barley Straw (kg)",
                "fan_lucerna": "Alfalfa Hay (kg)",
                "porumb_siloz": "Corn Silage (kg)",
                "uruiala_porumb": "Corn Cob (kg)",
                "uruiala_orz": "Barley Flour (kg)",
                "srot_rapita": "Srot Rapeseed (kg)",
                "tarate_grau": "Wheat Bran (kg)",
                "number_Animals": "Number of livestock",
                "GE": "GE - Gross Energy (kcal/day)",
                "DE": "DE - Digestible Energy (kcal/day)",
                "DE_Percent": "DE %",
                "YM": "Ym",
                "Em_EntericFerm_CH4": "CH₄ Enteric Fermentation Emissions (T/year)",
                "UE": "Urinary Energy as a percentage of GE (%)",
                "System1": "Waste Managed through Solid Storage (%)",
                "System2": "Waste Managed on Paddock/Pasture (%)",
                "System3": "Waste Managed as Slurry/Liquid (%)",
                "Em_direct_CH4": "CH₄ Direct Emssions (T/year)",
                "TAM": "TAM - Weight for individual livestock (kg)",
                "Nex": "Nex - N excretion/animal  (kg/animal/year)",
                "Em_direct_N2O": "N₂O Direct Emissions (kg/year)",
                "Frac_gas_sys1": "FracGas for Solid Waste (%)",
                "Frac_gas_sys3": "FracGas for Pasture/Paddock Waste (%)",
                "Frac_gas_sys2": "FracGas for Liquid/Slurry Waste (%)",
                "Em_indirect_N2O": "N₂O Volatilisation Emissisons (kg/year)",
                "Em_leaching_N2O": "N₂O Leaching Emissions (kg/year)",
                "Frac_leach_sys1": "FracLeach for Solid Waste (%)",
                "Frac_leach_sys2": "FracLeach for Pasture/Paddock Waste (%)",
                "Frac_leach_sys3": "FracLeach for Liquid/Slurry (%)"
                # Add more renames for Entries columns as necessary
            }
            df_entries = pd.DataFrame(entries, columns=entry_columns)[desired_order]
            df_entries = df_entries.rename(columns=renamed_entry_columns)
            df1_entries=df_entries.drop(columns= ["ID",	"submission_id", "CH₄ Enteric Fermentation Emissions (T/year)",	"CH₄ Direct Emssions (T/year)", "N₂O Direct Emissions (kg/year)","N₂O Volatilisation Emissisons (kg/year)", "N₂O Leaching Emissions (kg/year)"])
            df2_entries=df_entries.drop(columns= ["ID", "submission_id","Barley Straw (kg)","Alfalfa Hay (kg)","Corn Silage (kg)","Corn Cob (kg)","Barley Flour (kg)","Srot Rapeseed (kg)","Wheat Bran (kg)","Number of livestock","GE - Gross Energy (kcal/day)","DE - Digestible Energy (kcal/day)","DE %","EF", "Ym","Urinary Energy as a percentage of GE (%)","Waste Managed through Solid Storage (%)","Waste Managed on Paddock/Pasture (%)","Waste Managed as Slurry/Liquid (%)","TAM - Weight for individual livestock (kg)","Nex - N excretion/animal  (kg/animal/year)","FracGas for Solid Waste (%)","FracGas for Pasture/Paddock Waste (%)","FracGas for Liquid/Slurry Waste (%)", "FracLeach for Solid Waste (%)","FracLeach for Pasture/Paddock Waste (%)","FracLeach for Liquid/Slurry (%)"])
            GWP_CH4 = 25
            GWP_N2O = 298
            df2_entries['Total emissions/category (CO₂eq T/year)']=df2_entries['CH₄ Enteric Fermentation Emissions (T/year)']*GWP_CH4+df2_entries['CH₄ Direct Emssions (T/year)']*GWP_CH4+(df2_entries['N₂O Direct Emissions (kg/year)']/1000)*GWP_N2O+(df2_entries['N₂O Volatilisation Emissisons (kg/year)']/1000)*GWP_N2O+(df2_entries['N₂O Leaching Emissions (kg/year)']/1000)*GWP_N2O
            # Move the last column (Total emissions/category (CO2eq))to be the second one
            cols = df2_entries.columns.tolist()
            cols = [cols[0]] + [cols[-1]] + cols[1:-1]
            df2_entries = df2_entries[cols]
            # Display entries for the current submission using Streamlit's table function, indented
            # st.markdown('<div style="margin-left: 20px;">', unsafe_allow_html=True)

            st.write('**<h4 style="margin-left:10px;">Inputs & Intermediary metrics:**', unsafe_allow_html=True)
            # st.dataframe(df1_entries,hide_index=True)
            st.write('<h4 style="margin-left:60px;">• Energy and Soil Inputs', unsafe_allow_html=True)
            st.dataframe(df_submission_input)
            st.write('<h4 style="margin-left:60px;">• Livestock Inputs', unsafe_allow_html=True)
            st.dataframe(df1_entries)
            st.write('**<h4 style="margin-left:10px;">Emissions Outputs**', unsafe_allow_html=True)
            st.write('<h4 style="margin-left:60px;">• Livestock Emissions Outputs', unsafe_allow_html=True)

            if show_CO2e:
                df2_CO2e=df2_entries.copy()
                df2_CO2e['CH₄ Enteric Fermentation Emissions (T/year)']=df2_CO2e['CH₄ Enteric Fermentation Emissions (T/year)']*GWP_CH4
                df2_CO2e['CH₄ Direct Emssions (T/year)']=df2_CO2e['CH₄ Direct Emssions (T/year)']*GWP_CH4
                df2_CO2e['N₂O Direct Emissions (kg/year)']=(df2_CO2e['N₂O Direct Emissions (kg/year)']/1000)*GWP_N2O
                df2_CO2e['N₂O Volatilisation Emissisons (kg/year)']=(df2_CO2e['N₂O Volatilisation Emissisons (kg/year)']/1000)*GWP_N2O
                df2_CO2e['N₂O Leaching Emissions (kg/year)']=(df2_CO2e['N₂O Leaching Emissions (kg/year)']/1000)*GWP_N2O
                df2_CO2e = df2_CO2e.rename(columns={"CH₄ Enteric Fermentation Emissions (T/year)":"CH₄ Enteric Fermentation Emissions (CO₂eq T/year)" ,"CH₄ Direct Emssions (T/year)":"CH₄ Direct Emssions (CO₂eq T/year)", "N₂O Direct Emissions (kg/year)":"N₂O Direct Emissions (CO₂eq T/year)","N₂O Volatilisation Emissisons (kg/year)":"N₂O Volatilisation Emissisons (CO₂eq T/year)", "N₂O Leaching Emissions (kg/year)":"N₂O Leaching Emissions (CO₂eq  T/year)"})
                # Compute the totals
                totals = df2_CO2e.select_dtypes(include=[float, int]).sum(axis=0)
                # Add "Total" for the string column and append the row to the DataFrame
                totals['Livestock Category'] = 'Total'
                df2_CO2e = pd.concat([df2_CO2e, pd.DataFrame(totals).T], ignore_index=True)
                styled_df = df2_CO2e.style.apply(highlight_last_row, axis=None)
                st.dataframe(
                    styled_df,
                    column_config={
                        "CH₄ Direct Emssions (CO₂eq)": st.column_config.NumberColumn(
                            help="Direct CH₄ Emissions from manure management"
                        )
                    },
                    hide_index=True,
                )
                excel_df_livestock=styled_df




                # st.table(df2_CO2e)
            else:
                # Compute the totals
                totals = df2_entries.select_dtypes(include=[float, int]).sum(axis=0)
                # Add "Total" for the string column and append the row to the DataFrame
                totals['Livestock Category'] = 'Total'
                df2_entries = pd.concat([df2_entries, pd.DataFrame(totals).T], ignore_index=True)
                styled_df = df2_entries.style.apply(highlight_last_row, axis=None)
                styled_df
                st.dataframe(
                    styled_df,
                    column_config={
                        "CH₄ Direct Emssions (CO₂eq)": st.column_config.NumberColumn(
                            help="Direct CH₄ Emissions from manure management"
                        )
                    },
                    hide_index=True,
                )
                excel_df_livestock=styled_df
                # st.table(df2_entries)
            st.write('<h4 style="margin-left:60px;">• Energy Consumption Outputs', unsafe_allow_html=True)

            #Converting to CO2 emissions by multiplying with Emission Factor
            #EF for Electricity is 0.212 tonnes CO2/MWh
            df_submission_output_energy['Electricity (MWh/year)']=df_submission_output_energy['Electricity (MWh/year)']*0.212
            #EF for Gas = 0.05559 kg CO2/GJ; also need to convert metric cubes of user input to GigaJoules by *(38/1000)
            df_submission_output_energy['Natural gas (m³)']=(df_submission_output_energy['Natural gas (m³)']*38*0.05559)/1000
            #EF for Gasoline/Petrol:  0.0023tonnes CO2/Litre + 0.016g CH4/Litre /1000000 * GWP_CH4(25) + 0.019g N2O/Litre /1000000 * GWP_N2O(298)
            df_submission_output_energy['Gasoline (L)']=df_submission_output_energy['Gasoline (L)']*0.0023+(df_submission_output_energy['Gasoline (L)']*0.016*25)/1000000+(df_submission_output_energy['Gasoline (L)']*0.019*298)/1000000
            #EF for Biogas will be considered 0
            df_submission_output_energy['Biogas (m³)']=df_submission_output_energy['Biogas (m³)']*0
            #EF for Diesel:  0.0027tonnes CO2/Litre + 0.003g CH4/Litre /1000000 * GWP_CH4(25) + 0.6g N2O/Litre /1000000 * GWP_N2O(298)
            df_submission_output_energy['Diesel (L)']= df_submission_output_energy['Diesel (L)']*0.0027+(df_submission_output_energy['Diesel (L)']*0.003*25)/1000000+(df_submission_output_energy['Diesel (L)']*0.6*298)/1000000
            df_submission_output_energy.columns= ("Electricity (CO₂ T/year)", "Natural gas (CO₂ T/year)", "Gasoline (CO₂ equivalents T/year)", "Biogas (CO₂ equivalents T/year)","Diesel (CO₂ equivalents T/year)" )
            df_submission_output_energy['Total']=df_submission_output_energy["Electricity (CO₂ T/year)"]+ df_submission_output_energy["Natural gas (CO₂ T/year)"]+ df_submission_output_energy["Gasoline (CO₂ equivalents T/year)"]+df_submission_output_energy ["Biogas (CO₂ equivalents T/year)"]+df_submission_output_energy["Diesel (CO₂ equivalents T/year)"]
            df_submission_output_energy = df_submission_output_energy.style.apply(lambda col: ['background-color: #ADD8E6' if col.name == 'Total' else '' for _ in col])
            st.dataframe(df_submission_output_energy, hide_index=True)
            st.write('<h4 style="margin-left:60px;">• Soil Emissions Outputs', unsafe_allow_html=True)

            # df_submissions_output_soil = df_submissions_output_soil.style.apply(lambda col: ['background-color: #ADD8E6' if col.name == 'Total' else '' for _ in col])
            if show_CO2e:
                    df_submissions_output_soil=(df_submissions_output_soil*GWP_N2O)/1000
                    df_submissions_output_soil = df_submissions_output_soil.rename(columns={'Direct N₂O Emissions from Soil (kg/year)':'Direct N₂O Emissions from Soil (CO₂eq T/year)' , 'Indirect N₂O Emissions from Soil (kg/year)':'Indirect N₂O Emissions from Soil (CO₂eq T/year)'})
                    df_submissions_output_soil = df_submissions_output_soil.style.apply(lambda col: ['background-color: #ADD8E6' if col.name == 'Total' else '' for _ in col])
                    st.dataframe(df_submissions_output_soil, hide_index=True)
                    excel_output_soil=df_submissions_output_soil

            else:
                    df_submissions_output_soil = df_submissions_output_soil.style.apply(lambda col: ['background-color: #ADD8E6' if col.name == 'Total' else '' for _ in col])
                    st.dataframe(df_submissions_output_soil, hide_index=True)
                    excel_output_soil=df_submissions_output_soil

            st.markdown('</div>', unsafe_allow_html=True)


            # List of dataframes and sheet names for EXCEL export
            dataframes = [df_submission_input, df1_entries, excel_df_livestock, df_submission_output_energy, df_submissions_output_soil]
            sheet_names = ['Input Energy & Soil', 'Input Livestock', 'Output Livestock', 'Output Energy', 'Output Soil']

            # Convert dataframes to excel
            excel_data = convert_dfs_to_excel(dataframes, sheet_names)

            # Provide download link
            st.download_button(
                key=i,
                label="Download data as Excel",
                data=excel_data,
                file_name=f"Submission_ID:{int(df_submission['ID'])}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )



    cursor.close()

    # Add horizontal scrolling for tables
    st.markdown("""
    <style>
    table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    conn.close()


def create_df_from_db_source_breakdown_b():
    # Connect to the database
    conn = sqlite3.connect('S4F_database.db')
    # Fetch data from the "Submissions" table
    query = """
        SELECT * FROM Submissions
        WHERE user = ?
        ORDER BY date, time

    """
    df = pd.read_sql(sql=query, con=conn, params=(st.session_state['username'],))
    conn.close()
    #Global Warming Potentials (GWP) to get CO2 equivalents value for each gas
    GWP_CH4 = 25
    GWP_N2O = 298
    # We also divide N2O totals by 1000 to tranform kg to tonnes
    df['Enteric_ferm_total']=df['Enteric_ferm_total']*GWP_CH4
    df['Mannure_management_total']=df['Mannure_management_total']*GWP_CH4
    df['N2O_direct_total']=(df['N2O_direct_total']/1000)*GWP_N2O
    df['N2O_loss_total']=(df['N2O_loss_total']/1000)*GWP_N2O
    df['N2O_leaching_total']=(df['N2O_leaching_total']/1000)*GWP_N2O
    return df

def create_df_from_db_source_breakdown_b():
    # Connect to the database
    conn = sqlite3.connect('S4F_database.db')
    # Fetch data from the "Submissions" table
    query ="""

    SELECT E.submission_id, E.Em_EntericFerm_CH4,
           E.Em_direct_CH4, E.Em_direct_N2O, E.Em_indirect_N2O, E.Em_leaching_N2O,
           S.user, S.date, S.time
    FROM Entries E
    JOIN Submissions S ON E.submission_id = S.id
    WHERE user = ?
    ORDER BY date, time

    """

    df = pd.read_sql(sql=query, con=conn, params=(st.session_state['username'],))
    grouped_df = df.groupby('submission_id').agg({
    'Em_EntericFerm_CH4': 'sum',
    'Em_direct_CH4': 'sum',
    'Em_direct_N2O': 'sum',
    'Em_indirect_N2O': 'sum',
    'Em_leaching_N2O': 'sum'
    }    )
    grouped_df = grouped_df.reset_index()
    conn.close()
    #Global Warming Potentials (GWP) to get CO2 equivalents value for each gas
    GWP_CH4 = 25
    GWP_N2O = 298
    # We also divide N2O totals by 1000 to tranform kg to tonnes
    grouped_df['Em_EntericFerm_CH4']=grouped_df['Em_EntericFerm_CH4']*GWP_CH4
    grouped_df['Em_direct_CH4']=grouped_df['Em_direct_CH4']*GWP_CH4
    grouped_df['Em_direct_N2O']=(grouped_df['Em_direct_N2O']/1000)*GWP_N2O
    grouped_df['Em_indirect_N2O']=(grouped_df['Em_indirect_N2O']/1000)*GWP_N2O
    grouped_df['Em_leaching_N2O']=(grouped_df['Em_leaching_N2O']/1000)*GWP_N2O

    return df

def create_df_from_db_source_breakdown():
    # 1. Connect to the database
    conn = sqlite3.connect("S4F_database.db")

    # 2. Get required columns and perform operations
    query = """
    SELECT E.submission_id, E.Livestock_category, E.Em_EntericFerm_CH4,
           E.Em_direct_CH4, E.Em_direct_N2O, E.Em_indirect_N2O, E.Em_leaching_N2O,
           S.user, S.date, S.time
    FROM Entries E
    JOIN Submissions S ON E.submission_id = S.id
    """

    df = pd.read_sql(query, conn)
    conn.close()
    df = df[df['user'] == st.session_state["username"]]

    GWP_CH4 = 25
    GWP_N2O = 298
    df["Em_EntericFerm_CH4"] *= GWP_CH4
    df["Em_direct_CH4"] *= GWP_CH4
    for col in ["Em_direct_N2O", "Em_indirect_N2O", "Em_leaching_N2O"]:
        df[col] = (df[col] / 1000) * GWP_N2O


    # 4. Group by submission_id
    df_temp = df.groupby("submission_id").agg({
        "date": "first",
        "time": "first",
        "user": "first",
        "Em_EntericFerm_CH4": "sum",
        "Em_direct_CH4": "sum",
        "Em_direct_N2O": "sum",
        "Em_indirect_N2O": "sum",
        "Em_leaching_N2O": "sum"
    }).reset_index()

    data={
        "submission_id": df_temp['submission_id'],
        "Em_EntericFerm_CH4": df_temp['Em_EntericFerm_CH4'] ,
        "Em_direct_CH4":df_temp['Em_direct_CH4'],
        "Em_direct_N2O":df_temp['Em_direct_N2O']  ,
        "Em_indirect_N2O": df_temp['Em_indirect_N2O'] ,
        "Em_leaching_N2O": df_temp['Em_leaching_N2O'],
        "date": df_temp['date'],
        "time": df_temp['time'],
        "user": df_temp['user'],
    }
    df1 = pd.DataFrame(data)
    # Constructing df1

    return df1

##################
def source_breakdown_bar_chart_NOTINUSE(df):
    st.write(df)

#     unique_submissions = df["submission_id"].tolist()
#    # livestock_categories = [col for col in df.columns if col.startswith("CO₂eq")]
#     n = len(unique_submissions)
#     number_list = list(range(n + 1))
#     # Prepare the traces (bars) for each Livestock category
#     traces = []
#     for proc in df.columns:
#         traces.append(
#             go.Bar(
#                 name=proc.replace("CO₂eq ", ""),
#                 x=number_list,
#                 y=df[proc].tolist(),
#                 hoverinfo='y+name',
#                 text=df[['submission_id', 'time', proc]].apply(lambda row: f'Submission ID: {row["submission_id"]}<br>Date: {row["time"]}<br>Emission Source: {proc}<br>Emission Value: {row[proc]:.2f}', axis=1).tolist(),
#                 hovertemplate='%{text}',
#                 showlegend=True,
#                 textposition='none'  # Hide text on the bars
#             )
#         )

#     # Calculating the total sum for each submission
#     total_sums = df[df.columns].sum(axis=1).tolist()
#     total_sums=np.round(total_sums,2)
#     string_list = [f"Total: {item}" for item in total_sums]
#     traces.append(
#         go.Scatter(
#             mode="text",
#             x=number_list,
#             y=total_sums,
#             text=string_list,
#             textposition='top center',
#             hoverinfo='skip', # no hover for this trace
#             showlegend=False
#         )
#     )

#     # Create the figure and update layout
#     fig = go.Figure(data=traces)



#     fig.update_layout(legend_title_text='Emission Type',
#         title="Livestock Emissions",
#         xaxis_title="Submission ID",
#         yaxis_title="Emission Totals CO₂eq (tonnes)",
#         barmode='stack',
#         paper_bgcolor='rgba(0,0,0,0)',
#         plot_bgcolor='rgba(0,0,0,0)',
#         legend=dict(
#             orientation="h",
#             yanchor="bottom",
#             y=1.02,
#             xanchor="right",
#             x=0.35,
#             font=dict(
#                 size=10  # Reducing the font size
#             )
#         ),
#         margin=dict(t=170, b=0, l=0, r=0)
#     )


#     fig.update_xaxes(
#         showticklabels=False,  # Hides the tick labels (numbers)
#         # title_text="Submissions"

#     )
#     # Display the figure in Streamlit
#     st.plotly_chart(fig,use_container_width=True )





def source_breakdown_bar_chart(df):
    #Source or 'Process' breakdown
    # Melt the dataframe to long format for easier plotting with plotly
    df=df.drop(columns=['date'])

    df.columns=['id','Enteric fermentation', 'Manure Management', 'N₂O direct', 'N₂O loss', 'N₂O leaching', 'time', 'user']
    unique_submissions = df["id"].tolist()
#    livestock_categories = [col for col in df.columns if col.startswith("CO₂eq")]
    n = len(unique_submissions)
    number_list = list(range(n))
    df["bar_order"]=number_list
    df_melted = df.melt(id_vars=['bar_order','id', 'time', 'user'],
                        value_vars=[ 'Enteric fermentation', 'Manure Management', 'N₂O direct', 'N₂O loss', 'N₂O leaching'])

    # Create grouped bar chart using plotly
    fig = px.bar(df_melted,
                 x='bar_order',
                 y='value',
                 color='variable',
                 labels={'value': 'Emission Values', 'variable': 'Emission Types','time':'Date', 'id':'Submission ID'},
                 hover_data={'time':True,'id':True,'bar_order':False},
                 title='Emissions by Submission')

    # Adjusting the layout to show legend title
    fig.update_layout(legend_title_text='Emission Type', title="Livestock Emissions",
        xaxis_title="Submission ID",
        yaxis_title="Emission Totals CO₂ (tonnes)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                size=10  # Reducing the font size
            )
        ),
            margin=dict(t=170, b=5, l=0, r=0)
    )

    fig.update_xaxes(
        showticklabels=False,

    )


    # Add total emissions label on top of each bar

    for submission_id in df['bar_order'].unique():
        total_emission = df[df['bar_order'] == submission_id].iloc[:, 1:6].sum(axis=1)
        total_emission=total_emission.sum(axis=0)
        if submission_id == -1:
            fig.add_annotation(text=f"Average: {total_emission:.2f}",
                           x=submission_id,
                           y=total_emission,
                           showarrow=False,
                           yshift=10)
        else:
            fig.add_annotation(text=f"Total: {total_emission:.2f}",
                            x=submission_id,
                            y=total_emission,
                            showarrow=False,
                            yshift=10)

    return fig




def create_df_from_db_livestockCat_breakdown():
    # Connect to the database
    conn = sqlite3.connect('S4F_database.db')

    # Extract data from the Submissions table
    submissions_df = pd.read_sql(sql="SELECT id as submission_id, date, time, user FROM Submissions WHERE user =?", con=conn, params=(st.session_state['username'],))

    # Extract data from the Entries table
    entries_df = pd.read_sql(sql="SELECT submission_id, Livestock_category, Em_EntericFerm_CH4, Em_direct_CH4, Em_direct_N2O, Em_indirect_N2O, Em_leaching_N2O FROM Entries", con=conn)

    #Global Warming Potentials (GWP) to get CO2 equivalents value for each gas
    GWP_CH4 = 25
    GWP_N2O = 298
    # We also divide N2O totals by 1000 to tranform kg to tonnes
    entries_df['Em_total_category']=(entries_df['Em_EntericFerm_CH4']+entries_df['Em_direct_CH4'])*GWP_CH4+(entries_df['Em_direct_N2O']/1000+entries_df['Em_indirect_N2O']/1000+entries_df['Em_leaching_N2O']/1000)*GWP_N2O
    # For each unique Livestock_category, create a new column in the submissions_df
    for category in entries_df['Livestock_category'].unique():
        # Create a temporary dataframe for each category
        temp_df = entries_df[entries_df['Livestock_category'] == category].copy()
        temp_df.rename(columns={"Em_total_category": f"CO₂eq {category}"}, inplace=True)
        # Merge the temporary dataframe with the submissions dataframe on submission_id
        submissions_df = submissions_df.merge(temp_df[['submission_id', f"CO₂eq {category}"]],
                                              on='submission_id',
                                              how='left')

    # Fill NaN values with 0
    for category in entries_df['Livestock_category'].unique():
        submissions_df[f"CO₂eq {category}"].fillna(0, inplace=True)
    conn.close()

    return submissions_df



def livestockCategory_breakdown_bar_chart(df):
    # Extract unique submissions and Livestock categories
    unique_submissions = df["submission_id"].tolist()
    livestock_categories = [col for col in df.columns if col.startswith("CO₂eq")]
    n = len(unique_submissions)
    number_list = list(range(n + 1))
    # Prepare the traces (bars) for each Livestock category
    traces = []
    for category in livestock_categories:
        traces.append(
            go.Bar(
                name=category.replace("CO₂eq ", ""),
                x=number_list,
                y=df[category].tolist(),
                hoverinfo='y+name',
                text=df[['submission_id', 'time', category]].apply(lambda row: f'Submission ID: {row["submission_id"]}<br>Date: {row["time"]}<br>Emission Source: {category}<br>Emission Value: {row[category]:.2f}', axis=1).tolist(),
                hovertemplate='%{text}',
                showlegend=True,
                textposition='none'  # Hide text on the bars
            )
        )

    # Calculating the total sum for each submission
    total_sums = df[livestock_categories].sum(axis=1).tolist()
    total_sums=np.round(total_sums,2)
    string_list = [f"Total: {item}" for item in total_sums]
    traces.append(
        go.Scatter(
            mode="text",
            x=number_list,
            y=total_sums,
            text=string_list,
            textposition='top center',
            hoverinfo='skip', # no hover for this trace
            showlegend=False
        )
    )

    # Create the figure and update layout
    fig = go.Figure(data=traces)



    fig.update_layout(legend_title_text='Emission Type',
        title="Livestock Emissions",
        xaxis_title="Submission ID",
        yaxis_title="Emission Totals CO₂eq (tonnes)",
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.35,
            font=dict(
                size=10  # Reducing the font size
            )
        ),
        margin=dict(t=170, b=0, l=0, r=0)
    )


    fig.update_xaxes(
        showticklabels=False,  # Hides the tick labels (numbers)
        # title_text="Submissions"

    )
    # Display the figure in Streamlit
    st.plotly_chart(fig,use_container_width=True )


def filter_dataframes_for_average_comparison ( df1, df2, ca,cb, c3, container1_5):
     # Create a unique list of labels for each submission for the multiselect dropdown
    submission_labels = df1.apply(lambda row: f"Submission: {row['submission_id']}, {row['time']}", axis=1).unique()

    # Use Streamlit's multiselect to let the user select submissions
    with container1_5:
            selected_label = st.selectbox('Select Submission', submission_labels)

    with ca:
        st.subheader("GHG/Capita vs. Average")
        chosen_columns=st.multiselect(label="Include:", options=["Indirect CH₄","Direct CH₄","Direct N₂O","Indirect N₂O","Leaching N₂O","Electricity","Gas","Gasoline/Petrol","Biogas","Soil Direct N₂O","Soil Indirect N₂O","Diesel"], default=["Indirect CH₄","Direct CH₄","Direct N₂O","Indirect N₂O","Leaching N₂O","Electricity","Gas","Gasoline/Petrol","Biogas","Soil Direct N₂O","Soil Indirect N₂O","Diesel"], label_visibility="hidden")

        dicti ={
        "Idirect CH₄ - Enteric fermentation": "Em_EntericFerm_CH4",
        "Direct CH₄ - Manure Management":"Em_direct_CH4",
        "Direct N₂O":"Em_direct_N2O",
        "Indirect N₂O":"Em_indirect_N2O",
        "Leaching N₂O":"Em_leaching_N2O",
        "Electricity":"Electric",
        "Gas":"Gas",
        "Gasoline/Petrol":"Gasoline",
        "Biogas":"Biogas",
        "Soil Direct N₂O":"soil_N2O_direct",
        "Soil Indirect N₂O":"soil_N2O_indirect",
        "Diesel":"Diesel"
        }
        for i in range(0,len(chosen_columns)):
            chosen_columns[i]=dicti.get(chosen_columns[i])

    cba, cbb=cb.columns(2)
    Calculate_emission_factors(selected_label, chosen_columns, cb, c3, cba,cbb, )

    # Extract the submission IDs from the selected labels
    selected_id = int(selected_label.split(",")[0].split(":")[1].strip())

    # Filter the dataframes
    filtered_df1 = df1[df1['submission_id']==selected_id]
    filtered_df2 = df2[df2['submission_id']==selected_id]

    return filtered_df1, filtered_df2



def filter_dataframes_by_submission(df1, df2):
    # Create a unique list of labels for each submission for the multiselect dropdown
    submission_labels = df1.apply(lambda row: f"Submission: {row['submission_id']}, {row['time']}", axis=1).unique()

    # Use Streamlit's multiselect to let the user select submissions
    selected_labels = st.multiselect('Select Submissions', submission_labels)
    # Extract the submission IDs from the selected labels
    selected_ids = [int(label.split(",")[0].split(":")[1].strip()) for label in selected_labels]
    # Filter the dataframes
    filtered_df1 = df1[df1['submission_id'].isin(selected_ids)]
    filtered_df2 = df2[df2['submission_id'].isin(selected_ids)]

    return filtered_df1, filtered_df2, selected_ids


def compute_averages():
    # 1. Connect to the database
    conn = sqlite3.connect("S4F_database.db")

    # 2. Get required columns and perform operations
    query = """
    SELECT E.submission_id, E.Livestock_category, E.Em_EntericFerm_CH4,
           E.Em_direct_CH4, E.Em_direct_N2O, E.Em_indirect_N2O, E.Em_leaching_N2O,
           S.user
    FROM Entries E
    JOIN Submissions S ON E.submission_id = S.id
    """
    df = pd.read_sql(query, conn)
    query2="""
        SELECT id, user, Electric, Gas, Gasoline, Biogas, Water, Waste, soil_N2O_direct, soil_N2O_indirect, Diesel
        From Submissions
    """
    df_energy_soil= pd.read_sql(query2, conn)
    conn.close()
    df = df[df['user'] != st.session_state["username"]]
    df_energy_soil=df_energy_soil[df_energy_soil['user'] != st.session_state["username"]]
    df_energy_soil=df_energy_soil.drop(columns=["user"])
    df_energy_soil=df_energy_soil.mean()

    #EF for Electricity is 0.212 tonnes CO2/MWh
    df_energy_soil['Electric']=df_energy_soil['Electric']*0.212
    #EF for Gas = 0.05559 kg CO2/GJ; also need to convert metric cubes of user input to GigaJoules by *(38/1000)
    df_energy_soil['Gas']=(df_energy_soil['Gas']*38*0.05559)/1000
    #EF for Gasoline/Petrol:  Conversion L->TJ: 0.000032 TJ/L Gasoline; EF(Gasoline)=69.3 tonnes CO2/TJ
    df_energy_soil['Gasoline']=df_energy_soil['Gasoline']*0.000032*69.3
    #EF for Biogas will be considered 0
    df_energy_soil['Biogas']=df_energy_soil['Biogas']*0
    #EF for Diesel: Conversion L->TJ: 0.000035 TJ/L; EF(Diesel)=74.1 tonnes CO2/TJ
    df_energy_soil['Diesel']= df_energy_soil['Diesel']*0.000035*74.1

    GWP_CH4 = 25
    GWP_N2O = 298
    df["Em_EntericFerm_CH4"] *= GWP_CH4
    df["Em_direct_CH4"] *= GWP_CH4
    for col in ["Em_direct_N2O", "Em_indirect_N2O", "Em_leaching_N2O"]:
        df[col] = (df[col] / 1000) * GWP_N2O
    for col in ['soil_N2O_direct', 'soil_N2O_indirect']:
        df_energy_soil[col]= (df_energy_soil[col] / 1000) * GWP_N2O

    df["total_category_CO2e"] = df[["Em_EntericFerm_CH4", "Em_direct_CH4", "Em_direct_N2O", "Em_indirect_N2O", "Em_leaching_N2O"]].sum(axis=1)
    # 3. Compute the required variables
    cow_totals = df[df["Livestock_category"] == "Dairy cow"]["total_category_CO2e"].sum()
    heifers_totals = df[df["Livestock_category"] == "Heifers & primiparous cattle"]["total_category_CO2e"].sum()
    young_totals = df[df["Livestock_category"] == "Young cattle(3–9 months old)"]["total_category_CO2e"].sum()
    submission_number = df["submission_id"].nunique()

    cow_avg = cow_totals / (submission_number)
    heifers_avg = heifers_totals / (submission_number)
    young_avg = young_totals / (submission_number)

    # 4. Group by submission_id
    df_temp = df.groupby("submission_id").agg({
        "Em_EntericFerm_CH4": "sum",
        "Em_direct_CH4": "sum",
        "Em_direct_N2O": "sum",
        "Em_indirect_N2O": "sum",
        "Em_leaching_N2O": "sum"
    })

    df_temp=df_temp.mean()
    data2={
        "submission_id": -1,
        "date": "N/A",
        "time": "N/A",
        "user": "N/A",
        "Em_EntericFerm_CH4": df_temp['Em_EntericFerm_CH4'] ,
        "Em_direct_CH4":df_temp['Em_direct_CH4'],
        "Em_direct_N2O":df_temp['Em_direct_N2O']  ,
        "Em_indirect_N2O": df_temp['Em_indirect_N2O'] ,
        "Em_leaching_N2O": df_temp['Em_leaching_N2O'],
        "Electric": df_energy_soil['Electric'],
        "Gas": df_energy_soil['Gas'],
        "Gasoline": df_energy_soil['Gasoline'],
        "Biogas": df_energy_soil['Biogas'],
        "Water": df_energy_soil['Water'],
        "Waste": df_energy_soil['Waste'],
        "soil_N2O_direct": df_energy_soil['soil_N2O_direct'],
        "soil_N2O_indirect": df_energy_soil['soil_N2O_indirect']
    }
    df2 = pd.DataFrame([data2])
    # Constructing df1
    data = {
        "submission_id": -1,
        "date": "N/A",
        "time": "N/A",
        "user": "N/A",
        "CO₂eq Dairy cow": cow_avg,
        "CO₂eq Heifers & primiparous cattle": heifers_avg,
        "CO₂eq Young cattle(3–9 months old)": young_avg,
        "Electric": df_energy_soil['Electric'],
        "Gas": df_energy_soil['Gas'],
        "Gasoline": df_energy_soil['Gasoline'],
        "Biogas": df_energy_soil['Biogas'],
        "Water": df_energy_soil['Water'],
        "Waste": df_energy_soil['Waste'],
        "soil_N2O_direct": df_energy_soil['soil_N2O_direct'],
        "soil_N2O_indirect": df_energy_soil['soil_N2O_indirect']
    }
    df1 = pd.DataFrame([data])

    return df2, df1

def compute_averages_b():
    # 1. Connect to the database
    conn = sqlite3.connect("S4F_database.db")

    # 2. Get required columns and perform operations
    query = """
    SELECT E.submission_id, E.Livestock_category, E.Em_EntericFerm_CH4,
           E.Em_direct_CH4, E.Em_direct_N2O, E.Em_indirect_N2O, E.Em_leaching_N2O,
           S.user
    FROM Entries E
    JOIN Submissions S ON E.submission_id = S.id
    """

    df = pd.read_sql(query, conn)
    conn.close()
    df = df[df['user'] != st.session_state["username"]]

    GWP_CH4 = 25
    GWP_N2O = 298
    df["Em_EntericFerm_CH4"] *= GWP_CH4
    df["Em_direct_CH4"] *= GWP_CH4
    for col in ["Em_direct_N2O", "Em_indirect_N2O", "Em_leaching_N2O"]:
        df[col] = (df[col] / 1000) * GWP_N2O

    df["total_category_CO2e"] = df[["Em_EntericFerm_CH4", "Em_direct_CH4", "Em_direct_N2O", "Em_indirect_N2O", "Em_leaching_N2O"]].sum(axis=1)
    # 3. Compute the required variables
    cow_totals = df[df["Livestock_category"] == "Dairy cow"]["total_category_CO2e"].sum()
    heifers_totals = df[df["Livestock_category"] == "Heifers & primiparous cattle"]["total_category_CO2e"].sum()
    young_totals = df[df["Livestock_category"] == "Young cattle(3–9 months old)"]["total_category_CO2e"].sum()
    submission_number = df["submission_id"].nunique()

    cow_avg = cow_totals / (submission_number)
    heifers_avg = heifers_totals / (submission_number)
    young_avg = young_totals / (submission_number)

    # 4. Group by submission_id
    df_temp = df.groupby("submission_id").agg({
        "Em_EntericFerm_CH4": "sum",
        "Em_direct_CH4": "sum",
        "Em_direct_N2O": "sum",
        "Em_indirect_N2O": "sum",
        "Em_leaching_N2O": "sum"
    })

    df_temp=df_temp.mean()
    data2={
        "submission_id": -1,
        "date": "N/A",
        "time": "N/A",
        "user": "N/A",
        "Em_EntericFerm_CH4": df_temp['Em_EntericFerm_CH4'] ,
        "Em_direct_CH4":df_temp['Em_direct_CH4'],
        "Em_direct_N2O":df_temp['Em_direct_N2O']  ,
        "Em_indirect_N2O": df_temp['Em_indirect_N2O'] ,
        "Em_leaching_N2O": df_temp['Em_leaching_N2O']
    }
    df2 = pd.DataFrame([data2])
    # Constructing df1
    data = {
        "submission_id": -1,
        "date": "N/A",
        "time": "N/A",
        "user": "N/A",
        "CO₂eq Dairy cow": cow_avg,
        "CO₂eq Heifers & primiparous cattle": heifers_avg,
        "CO₂eq Young cattle(3–9 months old)": young_avg
    }
    df1 = pd.DataFrame([data])

    return df2, df1

def pie_chart_source_breakdown (df):

    agg_funcs = {col: 'sum' if df[col].dtype == 'int64' else 'first' for col in df.columns if col != 'submission_id'}
    result = df.groupby('submission_id').agg(agg_funcs).reset_index()
    df=result.drop(columns=["submission_id", "Water", "Waste", "user"])
    df.columns=("CH₄ Enteric Fementation","CH₄ Manure Management", "N₂O direct", "N₂O loss", "N₂O leaching", "date", "time", "Electric","Gas","Gasoline","Biogas","Soil Direct N₂O","Soil Indirect N₂O")
    color_dict = {
    'CH₄ Enteric Fementation': 'RoyalBlue',
    'CH₄ Manure Management': 'LightSkyBlue',
    'N₂O direct': 'Red',
    'N₂O loss': 'LightPink',
    'N₂O leaching': 'LightSeaGreen'
    }
    column_colors = [color_dict[col] for col in df.columns[:5]]

    # Create a subplot with 1 row and 2 columns (side-by-side)
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])

    # Add pie chart for first row of the DataFrame to the first subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[0].values, name="Row 1", marker=dict(colors=column_colors), domain=dict(x=[0, 0.2])),
        1, 1
    )

    # Add pie chart for second row of the DataFrame to the second subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[1].values, name="Row 2", marker=dict(colors=column_colors), domain=dict(x=[0.6, 1])),
        1, 2
    )

    # Update layout for better appearance
    fig.update_layout(
        # title_text="Side-by-Side Pie Charts",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[
        dict(text='Average', x=0.18, y=0.95, font_size=20, showarrow=False),
        dict(text='You', x=0.82, y=0.95, font_size=20, showarrow=False)],
        margin=dict(t=0, b=0, l=50, r=0),
        # width=800,
        # height=400,

        )
    st.plotly_chart(fig, use_container_width=True)



def pie_chart_source_breakdown_b (df):

    agg_funcs = {col: 'sum' if df[col].dtype == 'int64' else 'first' for col in df.columns if col != 'submission_id'}
    result = df.groupby('submission_id').agg(agg_funcs).reset_index()
    df=result.drop(columns=["submission_id", "Water", "Waste", "user"])
    df.columns=("CH₄ Enteric Fementation","CH₄ Manure Management", "N₂O direct", "N₂O loss", "N₂O leaching", "date", "time", "Electric","Gas","Gasoline","Biogas","soil_N2O_direct","soil_N2O_indirect")
    color_dict = {
    'CH₄ Enteric Fementation': 'RoyalBlue',
    'CH₄ Manure Management': 'LightSkyBlue',
    'N₂O direct': 'Red',
    'N₂O loss': 'LightPink',
    'N₂O leaching': 'LightSeaGreen'


    }
    column_colors = [color_dict[col] for col in df.columns[:5]]

    # Create a subplot with 1 row and 2 columns (side-by-side)
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])

    # Add pie chart for first row of the DataFrame to the first subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[0].values, name="Row 1", marker=dict(colors=column_colors), domain=dict(x=[0, 0.2])),
        1, 1
    )

    # Add pie chart for second row of the DataFrame to the second subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[1].values, name="Row 2", marker=dict(colors=column_colors), domain=dict(x=[0.6, 1])),
        1, 2
    )

    # Update layout for better appearance
    fig.update_layout(
        # title_text="Side-by-Side Pie Charts",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[
        dict(text='Average', x=0.18, y=0.8, font_size=20, showarrow=False),
        dict(text='You', x=0.82, y=0.8, font_size=20, showarrow=False)],
        margin=dict(t=0, b=0, l=50, r=0),
        # width=800,
        # height=400,

        )
    st.plotly_chart(fig, use_container_width=True)



def pie_chart_livestock_breakdown (df):
    df.columns=("submission_id", "date", "time", "user", "Dairy cow CO₂eq", "Heifers & primiparous cattle CO₂eq", "Young cattle(3–9 months old) CO₂eq", "Electric","Gas","Gasoline","Biogas","Water","Waste","Soil Direct N₂O","Soil Indirect N₂O")
    df=df.drop(columns=["submission_id", "Water", "Waste", "user"])
    # Create a subplot with 1 row and 2 columns (side-by-side)
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])

    # Add pie chart for first row of the DataFrame to the first subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[0].values, name="Row 1"),
        1, 2
    )

    # Add pie chart for second row of the DataFrame to the second subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[1].values, name="Row 2"),
        1, 1
    )

    # Update layout for better appearance
    fig.update_layout(
        # title_text="Side-by-Side Pie Charts",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[
        dict(text='Average', x=0.18, y=0.95, font_size=20, showarrow=False),
        dict(text='You', x=0.82, y=0.95, font_size=20, showarrow=False)],
        margin=dict(t=0, b=0, l=50, r=0),
        # width=800,
        # height=400,

        )
    st.plotly_chart(fig, use_container_width=True)

def pie_chart_livestock_breakdown_b (df):

    df.columns=("submission_id", "date", "time", "user", "Dairy cow CO₂eq", "Heifers & primiparous cattle CO₂eq", "Young cattle(3–9 months old) CO₂eq")
    df=df.drop(columns=["submission_id"])
    # Create a subplot with 1 row and 2 columns (side-by-side)
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])

    # Add pie chart for first row of the DataFrame to the first subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[0].values, name="Row 1"),
        1, 2
    )

    # Add pie chart for second row of the DataFrame to the second subplot
    fig.add_trace(
        go.Pie(labels=df.columns, values=df.iloc[1].values, name="Row 2"),
        1, 1
    )

    # Update layout for better appearance
    fig.update_layout(
        # title_text="Side-by-Side Pie Charts",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[
        dict(text='Average', x=0.18, y=0.95, font_size=15, showarrow=False),
        dict(text='You', x=0.82, y=0.95, font_size=15, showarrow=False)],
        margin=dict(t=0, b=0, l=50, r=0),
        # width=800,
        # height=400,

        )
    st.plotly_chart(fig, use_container_width=True)


def Calculate_emission_factors( selected_submission_id, chosen_columns, cb, c3, cba, cbb):
    # 1. Connect to the database
    conn = sqlite3.connect('S4F_database.db')

    # 2. Get the specified columns from the database
    query = """
    SELECT submission_id,
           Em_EntericFerm_CH4,
           Em_direct_CH4,
           Em_direct_N2O,
           Em_indirect_N2O,
           Em_leaching_N2O,
           number_Animals

    FROM Entries
    """
    df = pd.read_sql(query, conn)

    query2 ="""
    SELECT id,
            Electric,
            Gas,
            Gasoline,
            Biogas,
            Water,
            Waste,
            soil_N2O_direct,
            soil_N2O_indirect,
            Diesel
    FROM Submissions
    """
    df2=pd.read_sql(query2, conn)


    # 3. Group by submission_id and sum the other columns
    df_grouped = df.groupby('submission_id').sum().reset_index()

    df_grouped = df_grouped.merge(df2, left_on='submission_id', right_on='id')
    selected_submission_id = int(selected_submission_id.split(",")[0].split(":")[1].strip())

    ##Plotting Waste, Water metrics
    df_water_waste=df_grouped[['Water',"Waste", "number_Animals", "submission_id"]]
    #Make sure we don't divide by 0 (number_Animals)
    df_water_waste=df_water_waste[df_water_waste['number_Animals']!=0]
    #Scale to number of Animals to get Waste &Water/capita
    df_water_waste['Waste']=df_water_waste['Waste']/df_water_waste['number_Animals']
    df_water_waste['Water']=df_water_waste['Water']/df_water_waste['number_Animals']

    average_waste = f"{df_water_waste['Waste'].mean():.2f}"
    average_water = f"{df_water_waste['Water'].mean():.2f}"

    water_selected_submission = float(df_water_waste['Water'][df_water_waste['submission_id']==selected_submission_id].iloc[0])
    waste_selected_submission = float(df_water_waste['Waste'][df_water_waste['submission_id']==selected_submission_id].iloc[0])
    with cba:
        st.write("### Waste/Capita")
        if waste_selected_submission > df_water_waste['Waste'].mean():
            st.metric( label="m³", value=f"{waste_selected_submission:.2f}", delta=f"Average = {average_waste}m³", delta_color="inverse")
        else:
            st.metric( label="m³", value=f"{waste_selected_submission:.2f}", delta=f"Average = {average_waste}m³")


    with cb:
        st.write("### Emissions Composition vs. Average")
    with cbb:
        st.write("### Water/Capita")
        if waste_selected_submission > df_water_waste['Water'].mean():
            st.metric( label="m³", value=f"{water_selected_submission:.2f}", delta=f"Average = {average_water}m³", delta_color="inverse")
        else:
            st.metric( label="m³", value=f"{water_selected_submission:.2f}", delta=f"Average = {average_water}m³")

    df_grouped.drop(columns=['id', 'Water', 'Waste'], axis=1, inplace=True)

    #Global Warming Potentials (GWP) to get CO2 equivalents value for each gas
    GWP_CH4 = 25
    GWP_N2O = 298

    # We also divide N2O totals by 1000 to tranform kg to tonnes
    df_grouped['Em_EntericFerm_CH4']=df_grouped['Em_EntericFerm_CH4']*GWP_CH4
    df_grouped['Em_direct_CH4']=df_grouped['Em_direct_CH4']*GWP_CH4
    df_grouped['Em_direct_N2O']=(df_grouped['Em_direct_N2O']/1000)*GWP_N2O
    df_grouped['Em_indirect_N2O']=(df_grouped['Em_indirect_N2O']/1000)*GWP_N2O
    df_grouped['Em_leaching_N2O']=(df_grouped['Em_leaching_N2O']/1000)*GWP_N2O
    df_grouped['Electric']= df_grouped['Electric']*0.212
    df_grouped['Gas']= (df_grouped['Gas']*38*0.05559)/1000
    df_grouped['Gasoline']= df_grouped['Gasoline']
    df_grouped['Biogas']= df_grouped['Biogas']*0
    df_grouped['soil_N2O_direct']= df_grouped['soil_N2O_direct']*GWP_N2O
    df_grouped['soil_N2O_indirect']= df_grouped['soil_N2O_indirect']*GWP_N2O
    df_grouped['Diesel']= df_grouped['Diesel']
    #Converting Soil N2O emissions to CO2 equivalents
    df_grouped['soil_N2O_direct']=(df_grouped['soil_N2O_direct']/1000)*GWP_N2O
    df_grouped['soil_N2O_indirect']=(df_grouped['soil_N2O_indirect']/1000)*GWP_N2O

############
    # 4. Add the new column

    columns_to_select = [col for col in chosen_columns if col in df.columns]
    df_grouped['Emission_Factor'] = df[columns_to_select].sum(axis=1)
    df_grouped=df_grouped[df_grouped['number_Animals']!=0]

    df_grouped['Emission_Factor']=df_grouped['Emission_Factor']/df_grouped['number_Animals']
    # df_grouped['Emission_Factor'] = (df_grouped['Em_EntericFerm_CH4'] +
    #                             df_grouped['Em_direct_CH4'] +
    #                             df_grouped['Em_direct_N2O'] +
    #                             df_grouped['Em_indirect_N2O'] +
    #                             df_grouped['Em_leaching_N2O']) / df_grouped['number_Animals']

    conn.close()

    df=df_grouped

    # Calculate the average value
    average_value = df['Emission_Factor'].mean()
    df.fillna(0, inplace=True)

    hist_data, bin_edges = np.histogram(df['Emission_Factor'], bins=6)
    # Compute the average and the specific submission_id's value
    specific_value = df[df['submission_id'] == selected_submission_id]['Emission_Factor'].iloc[0]

    # Decide color for the specific submission_id's value
    color = "green" if specific_value < average_value else "red"
    with c3:
        if color == "green":
            st.markdown(f"<h4 style='color:green;'>✅ Congratulations! You are emitting less than other farms on average in submission ID: {selected_submission_id}</h3>", unsafe_allow_html=True)

        elif color == "red":
            st.markdown(f"<h4 style='color:red;'>🚨 You are emitting more than other farms on average in submission ID: {selected_submission_id}</h3>", unsafe_allow_html=True)
            #st.write(f"**🚨 You are emitting more than other farms on average in submissssion ID: {selected_submission_id}**")


    kde = gaussian_kde(df['Emission_Factor'])
    x_vals = np.linspace(df['Emission_Factor'].min(), df['Emission_Factor'].max(), 1000)
    kde_vals = kde(x_vals)
    #kde_vals = kde(x_vals) * len(df['Emission_Factor']) * (x_vals[1] - x_vals[0])  # Scaling it to fit the histogram
    kde_vals = kde_vals * (max(hist_data) / max(kde_vals))
    # Plot the histogram
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bin_edges[:-1],
        y=hist_data,
        width=np.diff(bin_edges),
        name='Histogram'

    ))

    # Add the git  (PDF) - Kernel Density Estimation (KDE)
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=kde_vals,
        mode='lines',
        name='Density',
        line=dict(color='lightblue', width=2)
    ))

    # # Add the vertical line for the average
    # fig.add_shape(
    #     go.layout.Shape(
    #         type="line",
    #         x0=average_value,
    #         x1=average_value,
    #         y0=0,
    #         y1=max(hist_data),
    #         line=dict(color="blue", width=2)
    #     )
    # )

    # # Add the vertical line for the specific submission_id's value
    # fig.add_shape(
    #     go.layout.Shape(
    #         type="line",
    #         x0=specific_value,
    #         x1=specific_value,
    #         y0=0,
    #         y1=max(hist_data),
    #         line=dict(color=color, width=2)
    #     )
    # )

    # # Add tooltips for the vertical lines
    # fig.add_trace(go.Scatter(
    #     x=[average_value, specific_value],
    #     y=[max(hist_data) * 0.9] * 2,  # Displaying the tooltip at 90% of histogram's height
    #     text=[f"Average: {average_value:.2f}", f"Specific Value: {specific_value:.2f}"],
    #     mode="text",
    # ))

# Add the vertical lines for the average and specific values
    shapes = [
        # Line for average
        {
            'type': 'line',
            'x0': average_value,
            'x1': average_value,
            'y0': 0,
            'y1': max(hist_data),
            'line': {'color': 'blue', 'width': 2}
        },
        # Line for specific value
        {
            'type': 'line',
            'x0': specific_value,
            'x1': specific_value,
            'y0': 0,
            'y1': max(hist_data),
            'line': {'color': color, 'width': 2}
        }
    ]
    fig.update_layout(shapes=shapes)

    # Add tooltips for the vertical lines
    annotations = [
        # Tooltip for average
        {
            'x': average_value,
            'y': max(hist_data) * 0.6,
            'xref': 'x',
            'yref': 'y',
            'text': f"Average GHG emissions/capita for other farms: {average_value:.2f}",
            'showarrow': True,
            'font': {
                'color': 'blue',
                'size': 14
            },
            'bgcolor': 'lightblue',
            'bordercolor': 'blue',
            'borderwidth': 2
        },
        # Tooltip for specific value
        {
            'x': specific_value,
            'y': max(hist_data) * 0.9,
            'xref': 'x',
            'yref': 'y',
            'text': f"GHG emissions/capita for SubmissionID: {selected_submission_id}: {specific_value:.2f}",
            'showarrow': True,
            'font': {
                'color': color,
                'size': 14
            },
            'bgcolor': 'lightyellow' if color == 'green' else 'mistyrose',
            'bordercolor': color,
            'borderwidth': 2
        }
    ]
    fig.update_layout(annotations=annotations,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title_text="GHG emissions/capita distribution among population",
            xaxis_title="GHG/capita (Tonnes CO₂eq)",
            yaxis_title="Number of farms"
            )
    with c3:
        st.plotly_chart(fig, use_container_width=True)



def soil_energy_graphs(submission_ids, c2, c3):
        # Connect to the database
    conn = sqlite3.connect("S4F_database.db")
    query = f"""SELECT id, time, Electric, Gas, Gasoline, Biogas, Water, Waste, soil_N2O_direct, soil_N2O_indirect, Diesel
                FROM Submissions WHERE id IN ({','.join('?' for _ in submission_ids)})"""
    df = pd.read_sql_query(query, conn, params=submission_ids)
    conn.close()
    #Converting to CO2 emissions by multiplying with Emission Factor
    #EF for Electricity is 0.212 tonnes CO2/MWh
    df['Electric']=df['Electric']*0.212
    #EF for Gas = 0.05559 kg CO2/GJ; also need to convert metric cubes of user input to GigaJoules by *(38/1000)
    df['Gas']=(df['Gas']*38*0.05559)/1000
    #EF for Gasoline/Petrol:  0.0023tonnes CO2/Litre + 0.016g CH4/Litre /1000000 * GWP_CH4(25) + 0.019g N2O/Litre /1000000 * GWP_N2O(298)
    df['Gasoline']=df['Gasoline']*0.0023+(df['Gasoline']*0.016*25)/1000000+(df['Gasoline']*0.019*298)/1000000
    #EF for Biogas will be considered 0
    df['Biogas']=df['Biogas']*0
    #EF for Diesel:  0.0027tonnes CO2/Litre + 0.003g CH4/Litre /1000000 * GWP_CH4(25) + 0.6g N2O/Litre /1000000 * GWP_N2O(298)
    df['Diesel']= df['Diesel']*0.0027+(df['Diesel']*0.003*25)/1000000+(df['Diesel']*0.6*298)/1000000


    #Converting Soil N2O emissions (kg) to CO2 equivalents (tonnes)
    df['soil_N2O_direct']=df['soil_N2O_direct']*0.298
    df['soil_N2O_indirect']=df['soil_N2O_indirect']*0.298

    # Plotting the first bar chart

    total_sums1 = df[['Electric','Gas', 'Gasoline', 'Biogas', 'Diesel' ]].sum(axis=1).tolist()
    total_sums1=np.round(total_sums1,2)
    string_list = [f"Total: {item}" for item in total_sums1]

    fig1 = go.Figure(data=[
        go.Bar(name='Electric', x=df.index, y=df['Electric'], hoverinfo="y+name", text=df[['id', 'time', 'Electric']].apply(lambda row: f'Submission ID: {row["id"]}<br>Date: {row["time"]}<br>Emission Source: Electricity<br>Emission Value: {row["Electric"]:.2f}', axis=1).tolist(), hovertemplate='%{text}', showlegend=True, textposition='none'),
        go.Bar(name='Gas', x=df.index, y=df['Gas'], hoverinfo="y+name", text=df[['id', 'time', 'Gas']].apply(lambda row: f'Submission ID: {row["id"]}<br>Date: {row["time"]}<br>Emission Source: Gas<br>Emission Value: {row["Gas"]:.2f}', axis=1).tolist(), hovertemplate='%{text}', showlegend=True, textposition='none'),
        go.Bar(name='Gasoline', x=df.index, y=df['Gasoline'], hoverinfo="y+name", text=df[['id', 'time', 'Gasoline']].apply(lambda row: f'Submission ID: {row["id"]}<br>Date: {row["time"]}<br>Emission Source: Gasoline<br>Emission Value: {row["Gasoline"]:.2f}', axis=1).tolist(), hovertemplate='%{text}', showlegend=True, textposition='none'),
        go.Bar(name='Biogas', x=df.index, y=df['Biogas'], hoverinfo="y+name", text=df[['id', 'time', 'Biogas']].apply(lambda row: f'Submission ID: {row["id"]}<br>Date: {row["time"]}<br>Emission Source: Biogas<br>Emission Value: {row["Biogas"]:.2f}', axis=1).tolist(), hovertemplate='%{text}', showlegend=True, textposition='none'),
        go.Bar(name='Diesel', x=df.index, y=df['Diesel'], hoverinfo="y+name", text=df[['id', 'time', 'Diesel']].apply(lambda row: f'Submission ID: {row["id"]}<br>Date: {row["time"]}<br>Emission Source: Diesel<br>Emission Value: {row["Diesel"]:.2f}', axis=1).tolist(), hovertemplate='%{text}', showlegend=True, textposition='none'),
        go.Scatter(mode="text", x=df.index,y=total_sums1, text=string_list, textposition='top center', hoverinfo='skip', showlegend=False
        )
    ])

    fig1.update_xaxes(
        showticklabels=False  # Hides the tick labels (numbers)

    )

    fig1.update_layout(barmode='stack', title="Energy Emissions",xaxis_title="Submission ID",yaxis_title="Emission Totals CO₂eq (tonnes)", legend_title_text="Emission Type", legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                size=10
            )
        ),
        margin=dict(t=170, b=0, l=0, r=0))

    total_sums2 = df[['soil_N2O_direct','soil_N2O_indirect']].sum(axis=1).tolist()
    total_sums2=np.round(total_sums2,2)
    string_list2 = [f"Total: {item}" for item in total_sums2]

    # Plotting the Soil emissions bar chart
    fig2 = go.Figure(data=[
        go.Bar(name='Direct N₂O Soil', x=df.index, y=df['soil_N2O_direct'], hoverinfo="y+name", text=df[['id', 'time', 'soil_N2O_direct']].apply(lambda row: f'Submission ID: {row["id"]}<br>Date: {row["time"]}<br>Emission Type: Direct N₂O Soil<br>Emission Value: {row["soil_N2O_direct"]:.2f}', axis=1).tolist(), hovertemplate='%{text}', showlegend=True, textposition='none'),
        go.Bar(name='Indirect N₂O Soil', x=df.index, y=df['soil_N2O_indirect'], hoverinfo="y+name", text=df[['id', 'time', 'soil_N2O_indirect']].apply(lambda row: f'Submission ID: {row["id"]}<br>Date: {row["time"]}<br>Emission Type: Indirect N₂O Soil<br>Emission Value: {row["soil_N2O_indirect"]:.2f}', axis=1).tolist(), hovertemplate='%{text}', showlegend=True, textposition='none'),
        go.Scatter(mode="text", x=df.index,y=total_sums2, text=string_list2, textposition='top center', hoverinfo='skip', showlegend=False)

    ])


    fig2.update_xaxes(
        showticklabels=False  # Hides the tick labels (numbers)
    )
    fig2.update_layout(barmode='stack', title="Soil Emissions", xaxis_title="Submission ID", yaxis_title="Emission Totals CO₂eq (tonnes)", legend_title_text="Emission Type", legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                size=10  # Reducing the font size
            )
        )
      ,margin=dict(t=170, b=0.01, l=0, r=0)
        )

    with c2:
        st.plotly_chart(fig1, use_container_width=True)
    with c3:
        st.plotly_chart(fig2, use_container_width=True)


def capture_page():
    # Chrome driver settings
    chrome_options = wd.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    browser = wd.Chrome(options=chrome_options)
    browser.get('http://localhost:8502')  # Adjust to your server URL if different

    # Get the rendered HTML content of your Streamlit app
    html_content = browser.page_source
    browser.quit()

    return html_content



def show():

        if st.session_state['authentication_status']==True:
            st.markdown("# Dashboard")
            # st.markdown("### **Submission History**")
            # expander = st.expander("**Submission History** - Click to expand")
            # with expander:
            tab1, tab2= st.tabs(["Interactive Dashboard", "Tabular Data"])
            with tab2:
                show_previous_submissions()
            with tab1:

                #PDF EXPORT BUTTON _ UDER CONSTRUCTION
                with open('/Users/yolandalaurent/code/ylaurent98/s4f/style.css') as f:
                    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
                pdf_io = io.BytesIO()
                if st.download_button( key='hi',label="Download PDF",data=pdf_io,file_name="streamlit_app.pdf",mime="application/pdf"):
                    html_content = capture_page()
                    # Generate PDF content in memory
                    HTML(string=html_content).write_pdf(pdf_io)
                    pdf_io.seek(0)  # Go back to the start of the BytesIO objec


                #get df from database to showing submissions broken down by source
                df1= create_df_from_db_source_breakdown()
                df1_avg=df1
                #get df from database to showing submissions broken down by livestock category
                df2 = create_df_from_db_livestockCat_breakdown()
                df2_avg=df2

                container1=st.container()
                with container1:
                    st.markdown("## Compare with previous sumbissions")
                    #filter above df's after user selects submissions to compare and display
                    filtered_df1, filtered_df2, submission_ids = filter_dataframes_by_submission (df2, df1)
                    c1, c2, c3 = st.columns(3)
                    con1= c1.container()
                    con2=c1.container()

                    with con2:
                        option= st.radio(label='Emissions Breakdown by', options=['Livestock category', 'Process'], horizontal=True, key='option')
                    with con1:
                        if option == 'Process':
                            #Plotting bar charts chronologically showing emission breakdowns by source/process
                            st.plotly_chart(source_breakdown_bar_chart(filtered_df2),use_container_width=True)
                        elif option=='Livestock category':
                            #by livestock category
                            livestockCategory_breakdown_bar_chart(filtered_df1)
                    soil_energy_graphs(submission_ids, c2, c3)
                container1_5=st.container()
                container2=st.container()
                container3=st.container()
                with container1_5:
                    st.markdown("## Compare with other farms")
                ca,cb=container2.columns(2)
                c3,c4=container3.columns(2)
                filtered_df1_avg, filtered_df2_avg= filter_dataframes_for_average_comparison (df2_avg, df1_avg, ca, cb, c3, container1_5)
                with c4:
                        # st.write("### Your Emissions Composition vs. Average")
                        df2_avg_row, df1_avg_row=compute_averages()
                        filtered_df1_avg = pd.concat([filtered_df1_avg, df1_avg_row])
                        filtered_df2_avg = pd.concat([filtered_df2_avg, df2_avg_row])
                        option_avg= st.radio('Livestock Emissions Breakdown by',['Livestock category', 'Process'], horizontal=True, key="option_avg")
                        if option_avg == 'Process':
                                #Plotting bar charts chronologically showing emission breakdowns
                                #by source
                                # st.markdown("### Breakdown by source ")
                                # st.write(df1)
                                # st.plotly_chart(source_breakdown_bar_chart(filtered_df2_avg), use_container_width=True)
                                pie_chart_source_breakdown(filtered_df2_avg)
                        elif option_avg=='Livestock category':
                                #by livestock category
                                # st.markdown("### Breakdown by livestock category ")
                                # st.write(df2)
                                # livestockCategory_breakdown_bar_chart(filtered_df1_avg)
                                pie_chart_livestock_breakdown(filtered_df1_avg)



        else:
            st.markdown("### Please log-in to view you dashboard")
