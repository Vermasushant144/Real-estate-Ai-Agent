import streamlit as st
from typing import List
from pydantic import BaseModel, Field
from firecrawl import FirecrawlApp
import os
from dotenv import load_dotenv

# -------------------------------
# Load API Key from .env
# -------------------------------
load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

if not FIRECRAWL_API_KEY:
    st.error("❌ FIRECRAWL_API_KEY not found in .env file. Please add it and restart the app.")
    st.stop()

# -------------------------------
# Data Models using Pydantic
# -------------------------------

class PropertyData(BaseModel):
    building_name: str = Field(description="Name of the building/property", alias="Building_name")
    property_type: str = Field(description="Type of property (commercial, residential, etc)", alias="Property_type")
    location_address: str = Field(description="Complete address of the property")
    price: str = Field(description="Price of the property", alias="Price")
    description: str = Field(description="Detailed description of the property", alias="Description")
    sku: str = Field(description="Unique Stock Keeping Unit for the property", alias="SKU")

class PropertiesResponse(BaseModel):
    properties: List[PropertyData] = Field(description="List of property details")

# -------------------------------
# Firecrawl Property Agent
# -------------------------------

class PropertyFindingAgent:
    def __init__(self, firecrawl_api_key: str):
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

    def find_properties(self, city: str, max_price: float,
                        property_category: str = "Residential", property_type: str = "Flat") -> List[PropertyData]:
        formatted_location = city.lower()

        urls = [
            f"https://www.squareyards.com/sale/property-for-sale-in-{formatted_location}/*",
            f"https://www.99acres.com/property-in-{formatted_location}-ffid/*",
            f"https://housing.com/in/buy/{formatted_location}/{formatted_location}",
        ]

        property_type_prompt = "Flats" if property_type == "Flat" else "Individual Houses"

        try:
            raw_response = self.firecrawl.extract(
                urls=urls,
                prompt=f"""Extract ONLY 10 OR LESS different {property_category} {property_type_prompt} from {city} that cost less than {max_price} crores.

Requirements:
- Property Category: {property_category} only
- Property Type: {property_type_prompt} only
- Location: {city}
- Maximum Price: {max_price} crores
- Include complete property details with exact location
- Include a unique SKU (Stock Keeping Unit) identifier for each property
- Minimum 3 and Maximum 10 properties
- Format: List of properties with their respective details
""",
                schema=PropertiesResponse.model_json_schema()
            )

            st.write("🔍 Raw Firecrawl API Response:", raw_response)

            if isinstance(raw_response, dict) and raw_response.get('success'):
                properties = raw_response['data'].get('properties', [])
                if not properties:
                    st.warning("🚫 No properties returned. Try different filters.")
                    return []
                return [PropertyData(**prop) for prop in properties]
            else:
                st.warning("⚠️ Firecrawl API did not return a successful response.")
                return []

        except Exception as e:
            st.error(f"❌ Error occurred: {e}")
            return []

# -------------------------------
# Streamlit App
# -------------------------------

def main():
    st.set_page_config(page_title="AI Real Estate Agent", page_icon="🏠", layout="wide")

    st.title("🏠 AI Real Estate Agent")
    st.info("Enter your criteria to get real-time property recommendations.")

    agent = PropertyFindingAgent(firecrawl_api_key=FIRECRAWL_API_KEY)

    col1, col2 = st.columns(2)

    with col1:
        city = st.text_input("City", placeholder="e.g., Bangalore")
        property_category = st.selectbox("Property Category", ["Residential", "Commercial"])

    with col2:
        max_price = st.number_input("Maximum Price (in Crores)", 0.1, 100.0, value=5.0, step=0.1)
        property_type = st.selectbox("Property Type", ["Flat", "Individual House"])

    if st.button("🔍 Start Search", use_container_width=True):
        if not city:
            st.error("⚠️ Please enter a city.")
            return

        with st.spinner("🔍 Fetching properties..."):
            property_results = agent.find_properties(
                city=city,
                max_price=max_price,
                property_category=property_category,
                property_type=property_type
            )

        st.success("✅ Search Complete!")
        st.subheader("🏘️ Recommendations")

        if property_results:
            for prop in property_results:
                st.markdown(f"### {prop.building_name}")
                st.markdown(f"**Type**: {prop.property_type}")
                st.markdown(f"**Location**: {prop.location_address}")
                st.markdown(f"**Price**: {prop.price} Crores")
                st.text_input("SKU", value=prop.sku, disabled=True)
                st.markdown(f"**Description**: {prop.description}")
                st.divider()
        else:
            st.warning("No properties found. Try changing your search filters.")

if __name__ == "__main__":
    main()
