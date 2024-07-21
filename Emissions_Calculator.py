import streamlit as st
# st.set_page_config(page_title='Emisisons_Calculator', layout='centered')

from enum import Enum
import sqlite3
from sqlite3 import Error
import plotly.express as px
from cat_dropdown import instantiate_selectbox, remove_selected_item, save_selected_item



with open ('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
#write here all enums, when creating the field, field names will call this class and key to get the value
class EnumFieldType(Enum):

    paie_orz = "Quantity of barley straw fed to livestock category per day (kg)"
    fan_lucerna = "Quantity of alfalfa hay fed to livestock category per day (kg)"
    porumb_siloz = "Quantity of corn silage fed to livestock category per day (kg)"
    uruiala_porumb = "Quantity of corn cob fed to livestock category per day (kg)"
    uruiala_orz = "Quantity of barley flour fed to livestock category per day (kg)"
    srot_rapita = "Quantity of srot rapeseed fed to livestock category per day (kg)"
    tarate_grau = "Quantity of wheat bran fed to livestock category per day (kg)"
    number_Animals = "Livestock of species/category/subcategory"
    UE = "Urinary energy expressed as a fraction of gross energy (GE)"
    #MS_T_S_k ="the manure fraction of the T-category animals, which is treated using the S manure management system in the climatic region k"
    TAM = "Typical weight of a category T animal"
    MS = "Fraction of the total annual excretion of nitrogen for each animal of species/category T adminitered under the S manure management system"
    System1 ="Percent of waste that is mannaged through system S (S=solid)"
    System2 ="Percent of waste that is mannaged through system S (S=paddock/pasture)"
    System3= "Percent of waste that is mannaged through system S (S=liquid/slurry)"   ## System 1+2+3 must always be 100
    Example10 = "fraction of the total annual excretion of nitrogen for each animal of species/category T administered under the S manure management system MS(T,S)"
    Frac_gas_sys1 = "percentage of N of manure produced by category T of livestock, volatilised as NH3 and NOx under the S manure management system S=solid"
    Frac_gas_sys2 = "percentage of N of manure produced by category T of livestock, volatilised as NH3 and NOx under the S manure management system S=pasture/paddock"
    Frac_gas_sys3 = "percentage of N of manure produced by category T of livestock, volatilised as NH3 and NOx under the S manure management system S=liquid/slurry"
    Frac_leach_sys1 = "S = Solid: percent of managed manure nitrogen losses for livestock category T due to runoff and leaching during solid and liquid storage of manure (typical range 1-20%)"
    Frac_leach_sys2 = "S = Paddock/Pasture: percent of managed manure nitrogen losses for livestock category T due to runoff and leaching during solid and liquid storage of manure (typical range 1-20%)"
    Frac_leach_sys3 = "S = Liquid/Slury: percent of managed manure nitrogen losses for livestock category T due to runoff and leaching during solid and liquid storage of manure (typical range 1-20%)"

#Annual Average Population (days)
AAP = {
        'Dairy cow': 365,
        'Heifers & primiparous cattle':365,
        'Young cattle(3–9 months old)':180
}
BoT = {
        'Dairy cow': 0.24,
        'Heifers & primiparous cattle':0.17,
        'Young cattle(3–9 months old)':0.17
}

steps_dict = {
          0:'Enteric Fermentation',
          1:'Methane: Direct emissions from Manure Management',
          2:'N2O: Direct emissions from Manure Management',
          3:'N2O - Nitrogen loss through volatilisation following manure management',
          4:'N2O - Nitrogen loss by leaching following manure management'
}


def createIfNoExists(cursor):
    print("creat if no exists called")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Entries (
    id INTEGER PRIMARY KEY,
    submission_id INTEGER,
    Livestock_category TEXT,
    paie_orz NUMERIC,
    fan_lucerna NUMERIC,
    porumb_siloz NUMERIC,
    uruiala_porumb NUMERIC,
    uruiala_orz NUMERIC,
    srot_rapita NUMERIC,
    tarate_grau NUMERIC,
	number_Animals INTEGER,
	GE NUMERIC,
	DE NUMERIC,
	DE_Percent NUMERIC,
	EF NUMERIC,
	YM NUMERIC,
	Em_EntericFerm_CH4 NUMERIC,
	UE NUMERIC,
	System1 NUMERIC,
	System2 NUMERIC,
	System3 NUMERIC,
	Em_direct_CH4 NUMERIC,
	TAM NUMERIC,
	Nex NUMERIC,
	Em_direct_N2O NUMERIC,
	Frac_gas_sys1 NUMERIC,
	Frac_gas_sys3 NUMERIC,
	Frac_gas_sys2 NUMERIC,
	"Em_indirect_N2O" NUMERIC,
    Em_leaching_N2O NUMERIC,
    Frac_leach_sys1 NUMERIC,
    Frac_leach_sys2 NUMERIC,
    Frac_leach_sys3 NUMERIC,
    Em_leaching_N2O NUMERIC
    )'''
    )
    cursor.execute ('''
            CREATE TABLE IF NOT EXISTS Submissions(
                id INTEGER PRIMARY KEY,
                date TEXT DEFAULT CURRENT_DATE,
                time TEXT DEFAULT CURRENT_TIMESTAMP,
                user TEXT,
                FSN NUMERIC,
                FON NUMERIC,
                FCR NUMERIC,
                FSOM NUMERIC,
                Electric NUMERIC,
                Gas NUMERIC,
                Gasoline NUMERIC,
                Diesel NUMERIC,
                Biogas NUMERIC,
                Water NUMERIC,
                Waste NUMERIC,
                soil_N2O_direct NUMERIC,
                soil_N2O_indirect NUMERIC
                )'''
    )


# CH4 - Direct emissions from enteric fermentation
def calculate_module0(step):
    #kcal per gram of PB, GB, celB, SEN respectively
    pb_kcal = 5.72
    gb_kcal = 9.5
    celB_kcal = 4.79
    sen_kcal = 4.17

    #Gross Energy (GE) - MJ /day
    # Energy from barley straw = quantity of barley straw feed(kg) * (kcal in 1g of PB  *  number of grams of PB foud in 1 kg barley straw feed + kcal in 1g of GB * ... + ... + ... )
    # Energy from alfalfa hay = quantity ...
    # ....
    en_paie_orz = st.session_state['inputs'][step]['paie_orz']*(32*pb_kcal+14*gb_kcal+390*celB_kcal+381*sen_kcal)
    en_fan_lucerna = st.session_state['inputs'][step]['fan_lucerna']*(120*pb_kcal+30*gb_kcal+330*celB_kcal+340*sen_kcal)
    en_porumb_siloz = st.session_state['inputs'][step]['porumb_siloz']*(22*pb_kcal+8*gb_kcal+85*celB_kcal+127*sen_kcal)
    en_uruiala_porumb = st.session_state['inputs'][step]['uruiala_porumb']*(90*pb_kcal+40*gb_kcal+22*celB_kcal+710*sen_kcal)
    en_uruiala_orz = st.session_state['inputs'][step]['uruiala_orz']*(100*pb_kcal+20*gb_kcal+56*celB_kcal+678*sen_kcal)
    en_srot_rapita = st.session_state['inputs'][step]['srot_rapita']*(350*pb_kcal+25*gb_kcal+130*celB_kcal+312*sen_kcal)
    en_tarate_grau = st.session_state['inputs'][step]['tarate_grau']*(150*pb_kcal+40*gb_kcal+105*celB_kcal+530*sen_kcal)

    GE = (en_paie_orz+en_fan_lucerna+en_porumb_siloz+en_uruiala_porumb+en_uruiala_orz+en_srot_rapita+en_tarate_grau)/239
    st.session_state['inputs'][step]['GE'] = GE

    #Digestible Energy (DE)
    #We scale the number of kcals obtained from each type of nutrient from each type of feed by the percentage of nutrient that is actually digested
    #the scaling factor is specific to each type of nutrient and each type of feed
    pb_kcal_DE=5.79
    gb_kcal_DE=8.15
    celB_kcal_DE=4.42
    sen_kcal_DE=4.06
    DE_paie_orz = st.session_state['inputs'][step]['paie_orz']*(32*pb_kcal_DE*0.21+14*gb_kcal_DE*0.32+390*celB_kcal_DE*0.47+381*sen_kcal_DE*0.45)
    DE_fan_lucerna = st.session_state['inputs'][step]['fan_lucerna']*(120*pb_kcal_DE*0.66+30*gb_kcal_DE*0.43+330*celB_kcal_DE*0.42+340*sen_kcal_DE*0.6)
    DE_porumb_siloz = st.session_state['inputs'][step]['porumb_siloz']*(22*pb_kcal_DE*0.5+8*gb_kcal_DE*0.5+85*celB_kcal_DE*0.55+127*sen_kcal_DE*0.7)
    DE_uruiala_porumb = st.session_state['inputs'][step]['uruiala_porumb']*(90*pb_kcal_DE*0.72+40*gb_kcal_DE*0.89+22*celB_kcal_DE*0.5+710*sen_kcal_DE*0.93)
    DE_uruiala_orz = st.session_state['inputs'][step]['uruiala_orz']*(100*pb_kcal_DE*0.7+20*gb_kcal_DE*0.92+56*celB_kcal_DE*0.34+678*sen_kcal_DE*0.9)
    DE_srot_rapita = st.session_state['inputs'][step]['srot_rapita']*(350*pb_kcal_DE*0.83+25*gb_kcal_DE*0.79+130*celB_kcal_DE*0.88+312*sen_kcal_DE*0.8)
    DE_tarate_grau = st.session_state['inputs'][step]['tarate_grau']*(150*pb_kcal_DE*0.79+40*gb_kcal_DE*0.71+105*celB_kcal_DE*0.25+530*sen_kcal_DE*0.71)

    DE = (DE_paie_orz+DE_fan_lucerna+DE_porumb_siloz+DE_uruiala_porumb+DE_uruiala_orz+DE_srot_rapita+DE_tarate_grau)/239
    st.session_state['inputs'][step]['DE']= DE


    ## User-defined: Annual Average Population = Number of livestock of category T scaled by number of days alive/year

    number=(st.session_state['inputs'][step]['number_Animals']/365)*AAP[st.session_state['category']]

    # the reference excel file notes the formula for DE% = (DE*GE)/100 but it seems wrong to me
    # Digestible Energy as a percentage of Gross Energy cosumption
    DE_Percent=(DE/GE)*100
    st.session_state['inputs'][step]['DE_Percent'] = DE_Percent

    ##Ecuation Cambra-Lopez, 2008
    ym = -0.0038 * (DE_Percent*DE_Percent) + 0.3501 * DE_Percent - 0.811
    st.session_state['inputs'][step]['YM'] = ym

    #CH4 EMISSION FACTOR FOR ENTERIC FERMENTATION PRODUCED BY A CATEGORY OF ANIMALS
    ef = (GE * (ym/100) * 365) / 55.65
    st.session_state['inputs'][step]['EF'] = ef

    #EMISSIONS CH4 (Tonnes/Year)
    Em_EntericFerm_CH4 = ef * (number / 1000)
    st.session_state['inputs'][step]['Em_EntericFerm_CH4'] = Em_EntericFerm_CH4

# CH4 - Direct emissions from manure management
def calculate_module1(step):
    ## implicit values
    # manure ash content calculated as a fraction of feed dry matter intake
    ash=0.08 #implicit value
    # maximum methane production capacity for manure produced by category T animals /m3 CH4 kg of VS excreted
    bo_t=BoT[st.session_state['category']] #implicit values found in BoT dictionary: daiy cows - industrial system: 0.24; heifers & primariparous: 0.17;  young: 0.17
    # methane conversion factors for each manure management system S by climate region k, %
    # mcf_s_k=[0.02, 0.01, 0.25] # implicit values for solid storage (pilot), pasture/paddock and liquid/slurry respectively
    mcf_s_k=[2, 1, 25]
    ## Get GE, DE_Percent calculated at previous step
    GE = st.session_state['inputs'][step-1]['GE']
    DE_Percent = st.session_state['inputs'][step-1]['DE_Percent']

    ##User-defined value UE : urinary energy expressed as a fraction of gross energy (GE) %
    # UE*GE - kcal
    UE = st.session_state['inputs'][step]['UE']

    # daily rate of excretion of volatile solids expressed as dry matter (kg VS/day)
    vs= (GE*(1-DE_Percent/100) + UE * GE)* ((1-ash)/18.45)

    ##User-defined values
    #Percentage of waste managed through solid system (S=solid)
    Percent_solid=st.session_state['inputs'][step]['System1']/100
    #Percentage of waste managed through paddock system (S=paddock/pasture)
    Percent_paddock=st.session_state['inputs'][step]['System2']/100
    #Percentage of waste managed through liquid system (S=liquid/slurry)
    Percent_liquid=st.session_state['inputs'][step]['System3']/100

    sum = (mcf_s_k[0]/100) * Percent_solid + (mcf_s_k[1]/100) * Percent_paddock + (mcf_s_k[2]/100) * Percent_liquid

    # annual emission factor of ch4 for a category of animals T (kg CH4/animal/day)
    ef_T= (vs*365)*bo_t*0.67*sum

    # User-defined from preious step: Annual Average Population = Number of livestock of category T scaled by number of days alive/year
    number=(st.session_state['inputs'][step-1]['number_Animals']/365)*AAP[st.session_state['category']]


    # CH4 emissions from manure management, for the defined population (Gg /year)
    Em_direct_CH4=(ef_T * number) /1000
    st.session_state['inputs'][step]['Em_direct_CH4']=Em_direct_CH4

# N2O - Direct emissions from manure management
def calculate_module2(step):

    ## Implicit values

    # rate of excretion of nitrogen used by default; 0.35 - dairy cows in Eastern Europe
    exc_rate = 0.35
    # factor for the direct emissions of N2O from the S manure management system; solid, paddock & liquid respectively - kg N2O-N/kg N
    # for dairy cows solid storage waste management system EF3=0.05 (pilot)
    factorEF3 =[0.005, 0, 0]


    ## User defined: typical weight of a category T animal - kg/animal
    weight = st.session_state['inputs'][step]['TAM']


    ## User-defined from previous steps:

    # Annual Average Population = Number of livestock of category T scaled by number of days alive/year
    number=(st.session_state['inputs'][step-2]['number_Animals']/365)*AAP[st.session_state['category']]
    # Percentage of waste managed through solid system (S=solid)
    Percent_solid = st.session_state['inputs'][step-1]['System1']/100
    # Percentage of waste managed through paddock system (S=paddock/pasture)
    Percent_paddock = st.session_state['inputs'][step-1]['System2']/100
    # Percentage of waste managed through liquid system (S=liquid/slurry)
    Percent_liquid = st.session_state['inputs'][step-1]['System3']/100
    # Percent_solid+ Percent_paddock + Percent_liquid = 1

    # annual excretion of N for animal category T - kg N/animal/year
    Nex = exc_rate * (weight / 1000) * 365
    st.session_state['inputs'][step]['Nex'] = Nex

    # direct emissions of N2O from manure management - kg N2O/year
    Em_direct_N2O= (44/28)* number * Nex * (factorEF3[0] * Percent_solid + factorEF3[1] * Percent_paddock + factorEF3[2] * Percent_liquid)
    st.session_state['inputs'][step]['Em_direct_N2O'] = Em_direct_N2O


# N2O - Nitrogen loss through volatilisation following manure management
def calculate_module3(step):
    ## Implicit values

    # factor for N2O from atmospheric deposition of N in soil and surface waters - kg N2O-N/kg NH3-N + NOx-N volatilised
    EF4 = 0.01

    # User-defined from preious step: Annual Average Population = Number of livestock of category T scaled by number of days alive/year
    number=(st.session_state['inputs'][step-3]['number_Animals']/365)*AAP[st.session_state['category']]

    # Get Nex fom previous step (average annual excretion of N per head of animal of the species/category T -  kg N/animal/year)
    Nex = st.session_state['inputs'][step-1]['Nex']  # Replace with the function call to get Nex(T) value from the module

    # User-defined from previous steps: MS(T,S): fraction of the total annual excretion of nitrogen for each animal of species/category T administered under the S manure management system
    # Percent_solid+ Percent_paddock + Percent_liquid = 1
    Percent_solid=st.session_state['inputs'][step-2]['System1']/100
    Percent_paddock=st.session_state['inputs'][step-2]['System2']/100
    Percent_liquid=st.session_state['inputs'][step-2]['System3']/100

    # User-defined: FracGasMS: percentage of N of manure produced by category T of livestock, volatilised as NH3 and NOx under the S manure management system
    # Solid waste storage system
    FracGasMS_sys1 = st.session_state['inputs'][step]['Frac_gas_sys1']/100
    # Paddock waste storage system
    FracGasMS_sys2 = st.session_state['inputs'][step]['Frac_gas_sys2']/100
    #liquid waste storage system
    FracGasMS_sys3 = st.session_state['inputs'][step]['Frac_gas_sys3']/100


    # N LOSSES DUE TO VOLATILISATION FROM MANURE MANAGEMENT:
    # Ecuation 10.26 adapted as such to reflect emissions from only one livestock category;
    # After user inputs forms for all categories, the calculated Em_indirect_N2O for each category will be summed up as "N2O_loss_total" in "calculate_module4()""
    # & INDIRECT N2O EMISSIONS DUE TO VOLATILISATION OF N FROM MANURE MANAGEMENT - kg N2O/year:
    # Ecuation 10.27; = EF4*(44/28)*Nvolatilization_MMS
    Em_indirect_N2O = EF4*(44/28)*number*Nex * (Percent_solid*FracGasMS_sys1 + Percent_paddock*FracGasMS_sys2 + Percent_liquid*FracGasMS_sys3)
    st.session_state['inputs'][step]['Em_indirect_N2O'] = Em_indirect_N2O

#N2O - Nitrogen loss by leaching following manure management

def calculate_module4(step):
    ## implicit values
    # emission factor for N2O emissions due to nitrogen laundering and leaching - kg N2O-N/kg N washed and leached
    EF5 = 0.0075

    # User-defined from preious step: Annual Average Population = Number of livestock of category T scaled by number of days alive/year
    number=(st.session_state['inputs'][step-4]['number_Animals']/365)*AAP[st.session_state['category']]

    # Get Nex - calculated in previous steps (module2): average annual excretion of N per head of animal of the species/category T - kg N/animal/year
    Nex= st.session_state['inputs'][step-2]['Nex']

    # User-defined from previous steps: MS(T,S): fraction of the total annual excretion of nitrogen for each animal of species/category T administered under the S manure management system
    # Percent_solid+ Percent_paddock + Percent_liquid = 1
    Percent_solid=st.session_state['inputs'][step-3]['System1']/100
    Percent_paddock=st.session_state['inputs'][step-3]['System2']/100
    Percent_liquid=st.session_state['inputs'][step-3]['System3']/100
    # User-defined: FracleachMS: percent of managed manure nitrogen losses for livestock category T due to runoff and leaching during solid and liquid storage of manure (typical range 1-20%)
    # Solid waste storage system
    FracleachMS_sys1 = st.session_state['inputs'][step]['Frac_leach_sys1']/100
    # Paddock waste storage system
    FracleachMS_sys2 = st.session_state['inputs'][step]['Frac_leach_sys2']/100
    #liquid waste storage system
    FracleachMS_sys3 = st.session_state['inputs'][step]['Frac_leach_sys3']/100

    # N LOSSES DUE TO LEACHING FROM MANURE MANAGEMENT SYSTEMS:
    # Ecuation 10.28 adapted as such to reflect emissions from only one livestock category;
    # After user inputs forms for all categories, the calculated Em_leaching_N2O for each category will be summed up as "N2O_leaching_total" below"
    # & INDIRECT N2O EMISSIONS DUE TO LEACHING FROM MANURE MANAGEMENT - kg N2O/year:
    # Ecuation 10.29; = EF4*(44/28)*Nleaching-MMS
    Em_leaching_N2O = EF5*(44/28)*number*Nex * (Percent_solid*FracleachMS_sys1 + Percent_paddock*FracleachMS_sys2 + Percent_liquid*FracleachMS_sys3)
    st.session_state['inputs'][step]['Em_leaching_N2O'] = Em_leaching_N2O


def getCategoriesFromDB():
    #modify this function to retrieve the list of categories defined by user, currently returning the bellow mock up categories
    return ['Dairy cow', 'Heifers & primiparous cattle', 'Young cattle(3–9 months old)']


calculation_functions = {
    0: calculate_module0,
    1: calculate_module1,
    2: calculate_module2,
    3: calculate_module3,
    4: calculate_module4,

}



# Define your Classes
class FieldType:
    def __init__(self):
        self.paie_orz = 0.0
        self.fan_lucerna = 0.0
        self.porumb_siloz = 0.0
        self.uruiala_porumb = 0.0
        self.uruiala_orz = 0.0
        self.srot_rapita = 0.0
        self.tarate_grau= 0.0
        self.number_Animals = 0.0


class FieldType2:
    def __init__(self):
        self.UE = 0.0
        self.System1 = 0.0
        self.System2 = 0.0
        self.System3 = 0.0

class FieldType3:
    def __init__(self):
        self.TAM = 0.0

class FieldType4:
    def __init__(self):
        self.Frac_gas_sys1 = 0.0
        self.Frac_gas_sys2 = 0.0
        self.Frac_gas_sys3 = 0.0

class FieldType5:
    def __init__(self):
        self.Frac_leach_sys1 = 0.0
        self.Frac_leach_sys2 = 0.0
        self.Frac_leach_sys3 = 0.0

# class FieldType6:
#     def __init__(self):
#         self.Example17 = 0.0
#         self.Example18 = 0.0
#         self.Example19 = 0.0
#         self.Example20 = 0.0

# class FieldType7:
#     def __init__(self):
#         self.Example21 = 0.0
#         self.Example22 = 0.0
#         self.Example23 = 0.0
#         self.Example24 = 0.0

# Database functions
def connect_db():
    conn = None;
    try:
        conn = sqlite3.connect('S4F_database.db')
    except Error as e:
        st.write(e)

    # if conn:
    #     st.write("Successful connection with the database")

    return conn

def close_db(conn):
    if conn:
        conn.close()


def save_form_to_db(cursor,conn):
    # # Here you'd save form_data under the category in your database.
    # conn.commit()
    createIfNoExists(cursor)
    conn.execute('PRAGMA busy_timeout = 10000')

    FSN = st.session_state['forms']['soil_energy']['FSN']
    FON = st.session_state['forms']['soil_energy']['FON']
    FCR = st.session_state['forms']['soil_energy']['FCR']
    FSOM = st.session_state['forms']['soil_energy']['FSOM']
    Electric = st.session_state['forms']['soil_energy']['Electric']
    Gas = st.session_state['forms']['soil_energy']['Gas']
    Gasoline = st.session_state['forms']['soil_energy']['Gasoline']
    Diesel = st.session_state['forms']['soil_energy']['Diesel']
    Biogas = st.session_state['forms']['soil_energy']['Biogas']
    Water = st.session_state['forms']['soil_energy']['Water']
    Waste = st.session_state['forms']['soil_energy']['Waste']
    Soil_direct = st.session_state['forms']['soil_energy']['N2O_direct']
    Soil_indirect = st.session_state['forms']['soil_energy']['N2O_indirect']

    cursor.execute("INSERT INTO Submissions (user, FSN, FON, FCR, FSOM, Electric, Gas, Gasoline, Biogas, Water, Waste, soil_N2O_direct, soil_N2O_indirect, Diesel) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (st.session_state['username'],FSN, FON, FCR, FSOM, Electric, Gas, Gasoline, Biogas, Water, Waste, Soil_direct, Soil_indirect, Diesel))
    cursor.execute("SELECT * FROM Submissions ORDER BY ROWID DESC LIMIT 1")
    last_row = cursor.fetchone()
    if last_row:
        submission_id=last_row['id']

    for key, value in st.session_state['forms'].items():
        if key != 'soil_energy':
            paie_orz = value.get('Step 1').get('paie_orz')
            fan_lucerna = value.get('Step 1').get('fan_lucerna')
            porumb_siloz = value.get('Step 1').get('porumb_siloz')
            uruiala_porumb = value.get('Step 1').get('uruiala_porumb')
            uruiala_orz = value.get('Step 1').get('uruiala_orz')
            srot_rapita = value.get('Step 1').get('srot_rapita')
            tarate_grau = value.get('Step 1').get('tarate_grau')
            number_Animals = value.get('Step 1').get('number_Animals')
            GE = value.get('Step 1').get('GE')
            DE = value.get('Step 1').get('DE')
            DE_Percent = value.get('Step 1').get('DE_Percent')
            EF = value.get('Step 1').get('EF')
            YM = value.get('Step 1').get('YM')
            Em_EntericFerm_CH4 = value.get('Step 1').get('Em_EntericFerm_CH4')
            UE = value.get('Step 2').get('UE')
            System1 = value.get('Step 2').get('System1')
            System2 = value.get('Step 2').get('System2')
            System3 = value.get('Step 2').get('System3')
            Em_direct_CH4 = value.get('Step 2').get('Em_direct_CH4')
            TAM = value.get('Step 3').get('TAM')
            Nex = value.get('Step 3').get('Nex')
            Em_direct_N2O = value.get('Step 3').get('Em_direct_N2O')
            Frac_gas_sys1 = value.get('Step 4').get('Frac_gas_sys1')
            Frac_gas_sys3 = value.get('Step 4').get('Frac_gas_sys3')
            Frac_gas_sys2 = value.get('Step 4').get('Frac_gas_sys2')
            Em_indirect_N2O = value.get('Step 4').get('Em_indirect_N2O')
            Frac_leach_sys1 = value.get('Step 5').get('Frac_leach_sys1')
            Frac_leach_sys2 = value.get('Step 5').get('Frac_leach_sys2')
            Frac_leach_sys3 = value.get('Step 5').get('Frac_leach_sys3')
            Em_leaching_N2O = value.get('Step 5').get('Em_leaching_N2O')
            Livestock_category = key
            cursor.execute("INSERT INTO Entries(submission_id, Livestock_category, paie_orz, fan_lucerna, porumb_siloz, uruiala_porumb, uruiala_orz, srot_rapita, tarate_grau, number_Animals, GE, DE, DE_Percent, EF, YM, Em_EntericFerm_CH4, UE, System1, System2, System3, Em_direct_CH4, TAM, Nex, Em_direct_N2O, Frac_gas_sys1, Frac_gas_sys3, Frac_gas_sys2, Em_indirect_N2O, Em_leaching_N2O, Frac_leach_sys1,Frac_leach_sys2,Frac_leach_sys3) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (submission_id, Livestock_category, paie_orz, fan_lucerna, porumb_siloz, uruiala_porumb, uruiala_orz, srot_rapita, tarate_grau, number_Animals, GE, DE, DE_Percent, EF, YM, Em_EntericFerm_CH4, UE, System1, System2, System3, Em_direct_CH4, TAM, Nex, Em_direct_N2O, Frac_gas_sys1, Frac_gas_sys3, Frac_gas_sys2, Em_indirect_N2O,Em_leaching_N2O,Frac_leach_sys1,Frac_leach_sys2,Frac_leach_sys3))
            conn.commit()



def buttonStartNewForm(buttonName):
    if(buttonName == "formCompletion"):
        st.session_state['start_form'] = False
        st.session_state['show_save_button'] = False
        st.session_state['dashboard']= False
    if st.button('Add cattle category',buttonName):
        st.session_state['start_form'] = True
        st.session_state['show_dropdown']= True
        st.session_state['category'] = ''
        st.session_state['step_completed'] = [False]*5
        st.session_state['inputs'] = [FieldType().__dict__, FieldType2().__dict__, FieldType3().__dict__, FieldType4().__dict__, FieldType5().__dict__]

def soil_calculations(FSN, FON, FCR, FSOM):
    EF1=0.01
    EF3=0.02
    FPRP=0
    for key, value in st.session_state['forms'].items():
        if key != "soil_energy":
            Nex=value.get('Step 3').get('Nex')
            N=(value.get('Step 1').get('number_Animals')/365)*AAP[key]
            MS_paddock=value.get('Step 2').get('System2')
            product=Nex*N*MS_paddock
            FPRP=FPRP+product
    N2O_direct=((FSN+FON+FCR+FSOM)*EF1+FPRP*EF3)*(44/28)
    EF4=0.1
    EF5=0.0075
    FracGasF=0.1
    FracGasM=0.2
    FracLeachH=0.3
    N2O_ATD=(FSN*FracGasF+(FON+FPRP)*FracGasM)*EF4
    N2O_L=(FSN+FON+FCR+FSOM+FPRP)*FracLeachH*EF5
    N2O_indirect=(N2O_ATD+N2O_L)*(44/28)
    st.session_state['forms']['soil_energy']['N2O_direct']=N2O_direct
    st.session_state['forms']['soil_energy']['N2O_indirect']=N2O_indirect

    # st.write('nex', Nex, 'n', N, 'ms_paddock', MS_paddock, "N2O", N2O_direct, "N2O indirect", N2O_indirect)


def saveToDataBaseButton(cursor,conn):
        if st.button('Final submission'):
            #save_form_to_db(conn, st.session_state['category'], st.session_state['forms'][st.session_state['category']])
            st.write("Submission successful. Please refresh page to make a new submission.")
            # st.markdown("[Go to Emissionss dashboard to see results(http://localhost:8501/other_page)")
            soil_calculations(st.session_state['forms']['soil_energy']['FSN'],st.session_state['forms']['soil_energy']['FON'],st.session_state['forms']['soil_energy']['FCR'], st.session_state['forms']['soil_energy']['FSOM'] )

            save_form_to_db(cursor,conn)
            # connn.commit()
            close_db(conn)


def buttonShowCurrentSessionState(cursor,conn):
    if st.button('Show current session state'):
        st.write('Current session state:')
        st.write(st.session_state['forms'])
        st.session_state['show_save_button'] = True
        st.session_state['dashboard'] = True


def category_selectbox():
    if 'show_dropdown' not in st.session_state:
        st.session_state.show_dropdown = True
    if st.session_state.show_dropdown:
        selected = instantiate_selectbox(st.session_state, st.session_state.current_values)
        if selected:  # Only act if a valid item is selected
            save_selected_item(st.session_state, selected)
            remove_selected_item(st.session_state, selected)
            st.session_state.show_dropdown = False  # Hide the dropdown once an item is selected
            st.experimental_rerun()




# Streamlit Application
def show():
    with open ('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    st.title("Greenhouse Gas Emissions Calculator")
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if 'current_values' not in st.session_state:
        st.session_state.current_values = getCategoriesFromDB()

    if 'forms' not in st.session_state:
        st.session_state['forms'] = {}

    ## user Input values for Soils and Energy comsumption

    # Initialize session state if it doesn't exist
    if 'soil_energy' not in st.session_state['forms']:
        st.session_state['forms']['soil_energy'] = None

    # Check if the form has been submitted before
    if st.session_state['forms']['soil_energy'] is None:
        # Create the numeric input form
        st.header("Emissions from agricultural soils")
        FSN = st.number_input('Enter quantity of synthetic fertilizers applied on the field (kg/yr)', format='%f')
        FON = st.number_input('Enter quantity of organic fertilizers applied on the ground (kg/yr)', format='%f')
        FCR = st.number_input('Enter annual amount of Nitrogen of crop residues (kg/yr)', format='%f')
        FSOM = st.number_input('Enter quantity of Nitrogen mineralized as a result of the change in the use of the land (kg/yr)', format='%f')
        st.header("Emissions from energy consumption")
        Electric = st.number_input('Enter electricity consumption (MWh/year)', format='%f')
        Gas = st.number_input('Enter natural gas consumption (m³/year)', format='%f')
        Gasoline = st.number_input('Enter petrol/gasoline consumption (Litres/year)', format='%f')
        Diesel = st.number_input('Enter diesel consumption (Litres/year)', format='%f')
        Biogas = st.number_input('Enter biogas conssumption (m³/year)', format='%f')
        Water = st.number_input('Enter water consumption (m³/year)', format='%f')
        Waste = st.number_input('Enter waste production (m³/year)', format='%f')

        if st.button('Submit'):
            # Store the data in session state after submission
            st.session_state['forms']['soil_energy'] = {
                'FSN': FSN,
                'FON': FON,
                'FCR': FCR,
                'FSOM': FSOM,
                'Electric': Electric,
                'Gas': Gas,
                'Gasoline': Gasoline,
                'Diesel' : Diesel,
                'Biogas': Biogas,
                'Water': Water,
                'Waste': Waste
            }
    if "Dairy cow" in st.session_state.forms:
                st.write("Dairy cow input saved!")
    if "Heifers & primiparous cattle" in st.session_state.forms:
                st.write("Heifers & Primiparous input saved!")
    if "Young cattle(3–9 months old)" in st.session_state.forms:
                st.write("Young cattle(3–9 months old) input saved!")

    if st.session_state['forms']['soil_energy']:
        st.write("Energy and Soils input saved!")
        # st.header("Emissions from Livestock")
        if st.session_state.current_values and len(st.session_state.current_values) > 0 and len(st.session_state.forms)<2:
                # session state has values
                buttonStartNewForm('formStart')
        # else:
        #         st.write('There are no more available categories to select from')

            # buttonShowCurrentSessionState(cursor,conn)

        if 'start_form' in st.session_state and st.session_state['start_form']:

                #st.session_state['category']= st.selectbox('Enter cattle category', ('Adult cattle ', 'Pregnant cattle & Heifers', 'Growing calves 3-9 months old'))
                category_selectbox()
                # Only display Steps if category field has been filled
                if st.session_state['category']:
                    st.header(f"Emissions from Livestock category: {st.session_state['category']}")
                    for step in range(5):
                        # Only display current step if the previous step has been completed
                        if step == 0 or st.session_state['step_completed'][step-1]:
                            st.subheader(steps_dict.get(step))

                            # Create an input for each item in the current step
                            for field_type in st.session_state['inputs'][step]:
                            # Exclude 'sum' field from the inputs as it's not part of EnumFieldType
                                if field_type != 'sum':
                                    if hasattr(EnumFieldType, field_type):
                                        new_input = st.number_input(f'Input {getattr(EnumFieldType, field_type).value}', value=st.session_state['inputs'][step][field_type], key=field_type, format='%.2f', min_value=0.0)
                                        if new_input != st.session_state['inputs'][step][field_type]:
                                            st.session_state['inputs'][step][field_type] = new_input

                            # Submit button for the current step
                            if st.button(f'Submit Step {step+1}'):
                                st.session_state['step_completed'][step] = True
                                # Calculate and store the calculations from the inputs for the current step within the inputs dictionary
                                calculation_function = calculation_functions.get(step)
                                if calculation_function:
                                    calculation_function(step)


                    # Button to save current form to the session state
                    if all(st.session_state['step_completed']):
                        st.session_state['forms'][st.session_state['category']] = {
                            'Step 1': st.session_state['inputs'][0],
                            'Step 2': st.session_state['inputs'][1],
                            'Step 3': st.session_state['inputs'][2],
                            'Step 4': st.session_state['inputs'][3],
                            'Step 5': st.session_state['inputs'][4],

                        }
                        st.session_state['show_save_button'] = True
                        st.session_state['dashboard'] = True



                        if st.session_state.current_values and len(st.session_state.current_values) > 0:
                            # session state has values
                            buttonStartNewForm('stepCompletion')
                        else:
                            st.write('There are no more available categories to select from')

                        # st.write(f"Form saved under category {st.session_state['category']}!")
                        #st.session_state['start_form'] = False  # Reset the form

        if 'show_save_button' in st.session_state and st.session_state['show_save_button']:
                saveToDataBaseButton(cursor,conn)


if __name__ == "__main__":
    show()
