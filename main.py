"""Convert 'sample_adobo_feed.xml' to the specified JSON format"""
import json
import xml.etree.ElementTree as ET

import requests


def load_properties_from_file(input_file):
    """Get a list of properties from the given XML file

    :param input_file: Path to the input XML file
    :return: A list of property elements
    """
    tree = ET.parse(input_file)
    root = tree.getroot()
    return root.findall("./Property")


def load_properties_from_url(url):
    """Get a list of properties from the given XML URL

    :param url: URL of the XML file
    :return: A list of property elements
    """
    xml_string = requests.get(url).text
    root = ET.fromstring(xml_string)
    return root.findall("./Property")


def property_city_filter(city):
    """Create a predicate for property elements based on the city

    :param city: City to compare against, case-insensitive
    :return: A predicate which may be used to filter properties by city
    """
    def inner(p):
        return p.find("./PropertyID/Address/City").text.lower().strip() == city.lower()

    return inner


def get_total_bedrooms(p):
    """Gets the total number of bedrooms for a given property element

    :param p: The property element
    :return: The total number of rooms at the property
    """
    def get_bedrooms_per_floorplan(fp):
        total_units = float(fp.find("./UnitCount").text)
        bedrooms_per_unit = float(fp.find("./Room[@RoomType='Bedroom']/Count").text)
        return total_units * bedrooms_per_unit

    floor_plans = p.findall("./Floorplan")
    bedrooms_per_floor_plan = map(get_bedrooms_per_floorplan, floor_plans)
    return sum(bedrooms_per_floor_plan)


def map_property_data(p):
    """Maps a property element to a JSON schema

    The schema is:
    {
        property_id: string,
        name: string,
        email: string,
        total_rooms: number
    }

    :param p: A single property element
    :return: The property mapped to the schema
    """
    return {
        "property_id": int(p.find("./PropertyID/Identification").attrib["IDValue"]),
        "name": p.find("./PropertyID/MarketingName").text,
        "email": p.find("./PropertyID/Email").text,
        "total_rooms": get_total_bedrooms(p)
    }


def write_property_data_to_json(property_data_list, output_file):
    """Writes a property JSON list to the given output file

    :param property_data_list: A list of property dictionaries
    :param output_file: Path to the output file
    """
    with open(output_file, "w") as output:
        json.dump(property_data_list, output)


def main():
    # load_properties can be easily changed to get data from a different source
    # load_properties = load_properties_from_file
    # input_location = "sample_abodo_feed.xml"
    load_properties = load_properties_from_url
    input_location = "https://s3.amazonaws.com/abodo-misc/sample_abodo_feed.xml"

    # write_properties can also be easily changed to work with something like a database
    write_properties = write_property_data_to_json
    output_location = "sample_abodo_feed.json"

    # Data pipeline is straightforward
    all_properties = load_properties(input_location)
    madison_properties = filter(property_city_filter("Madison"), all_properties)
    extracted_property_data = map(map_property_data, madison_properties)
    write_properties(list(extracted_property_data), output_location)


if __name__ == '__main__':
    main()
