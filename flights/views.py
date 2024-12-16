import os
from xml import etree
import xml.etree.ElementTree as ET
from datetime import datetime
from django.http import JsonResponse
from django.conf import settings


def load_flight_data():
    file1_path = os.path.join(settings.BASE_DIR, 'RS_ViaOW.xml')
    file2_path = os.path.join(settings.BASE_DIR, 'RS_Via-3.xml')

    if not os.path.exists(file1_path) or not os.path.exists(file2_path):
        raise FileNotFoundError("One or both XML files are missing.")

    flights_from_file1 = parse_xml(file1_path)
    flights_from_file2 = parse_xml(file2_path)

    filtered_file1 = filter_flights_by_route(flights_from_file1, "DXB", "BKK")
    filtered_file2 = filter_flights_by_route(flights_from_file2, "DXB", "BKK")

    return filtered_file1, filtered_file2

def filter_flights_by_route(flights, source, destination):
    """
    Фильтрует рейсы по заданным пунктам отправления и назначения.
    """
    filtered_flights = []
    for flight in flights:
        if (flight["segments"][0]["source"] == source and
                flight["segments"][-1]["destination"] == destination):
            filtered_flights.append(flight)
    return filtered_flights

def find_cheapest_and_expensive(flights):
    """
    Находит самый дешёвый и самый дорогой маршруты.
    """
    if not flights:
        return None, None

    # Поиск маршрутов с минимальной и максимальной ценой
    cheapest = min(flights, key=lambda x: x["total_price"])
    expensive = max(flights, key=lambda x: x["total_price"])

    return cheapest, expensive

def find_fastest_and_longest(flights):
    """
    Находит самый быстрый и самый долгий маршруты.
    """
    if not flights:
        return None, None

    # Функция для подсчёта общей продолжительности маршрута
    def calculate_total_duration(flight):
        total_seconds = 0
        for segment in flight["segments"]:
            dep_time = datetime.strptime(segment["departure_time"], "%Y-%m-%dT%H%M")
            arr_time = datetime.strptime(segment["arrival_time"], "%Y-%m-%dT%H%M")
            total_seconds += (arr_time - dep_time).total_seconds()
        return total_seconds

    # Поиск маршрутов с минимальной и максимальной продолжительностью
    fastest = min(flights, key=calculate_total_duration)
    longest = max(flights, key=calculate_total_duration)

    return fastest, longest



def get_filtered_flights(request):
    try:
        filtered_file1, filtered_file2 = load_flight_data()
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({
        "file1": filtered_file1,
        "file2": filtered_file2
    })

def get_cheapest_flights(request):
    try:
        filtered_file1, filtered_file2 = load_flight_data()
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=400)

    cheapest1, _ = find_cheapest_and_expensive(filtered_file1)
    cheapest2, _ = find_cheapest_and_expensive(filtered_file2)

    return JsonResponse({"file1": cheapest1, "file2": cheapest2})


def get_expensive_flights(request):
    try:
        filtered_file1, filtered_file2 = load_flight_data()
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=400)

    _, expensive1 = find_cheapest_and_expensive(filtered_file1)
    _, expensive2 = find_cheapest_and_expensive(filtered_file2)

    return JsonResponse({"file1": expensive1, "file2": expensive2})


def get_fastest_flights(request):
    try:
        filtered_file1, filtered_file2 = load_flight_data()
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=400)

    fastest1, _ = find_fastest_and_longest(filtered_file1)
    fastest2, _ = find_fastest_and_longest(filtered_file2)

    return JsonResponse({"file1": fastest1, "file2": fastest2})


def get_longest_flights(request):
    try:
        filtered_file1, filtered_file2 = load_flight_data()
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=400)

    _, longest1 = find_fastest_and_longest(filtered_file1)
    _, longest2 = find_fastest_and_longest(filtered_file2)

    return JsonResponse({"file1": longest1, "file2": longest2})

def compare_flights_view(request):
    try:
        filtered_file1, filtered_file2 = load_flight_data()
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=400)

    comparison_result = compare_flights(filtered_file1, filtered_file2)

    return JsonResponse(comparison_result)

def compare_flights(flights1, flights2):
    """
    Сравнивает два списка маршрутов и выделяет изменения:
    - Добавленные маршруты
    - Удаленные маршруты
    - Измененные маршруты (цена, продолжительность).
    """
    added = []
    removed = []
    modified = []

    # Преобразование списка маршрутов в ключи для сравнения
    def create_flight_key(flight):
        return (
            flight["segments"][0]["source"],
            flight["segments"][-1]["destination"],
            tuple((segment["carrier"], segment["flight_number"]) for segment in flight["segments"])
        )

    flights1_dict = {create_flight_key(flight): flight for flight in flights1}
    flights2_dict = {create_flight_key(flight): flight for flight in flights2}

    # Добавленные и измененные маршруты
    for key, flight2 in flights2_dict.items():
        if key not in flights1_dict:
            added.append(flight2)
        else:
            flight1 = flights1_dict[key]
            changes = {}

            # Сравнение цены
            if flight1["total_price"] != flight2["total_price"]:
                changes["price"] = {
                    "old": flight1["total_price"],
                    "new": flight2["total_price"]
                }

            # Сравнение продолжительности маршрута
            duration1 = sum(calculate_segment_duration(segment) for segment in flight1["segments"])
            duration2 = sum(calculate_segment_duration(segment) for segment in flight2["segments"])
            if duration1 != duration2:
                changes["duration"] = {
                    "old": format_duration(duration1),
                    "new": format_duration(duration2)
                }

            if changes:
                modified.append({
                    "route": key,
                    "changes": changes
                })

    # Удалённые маршруты
    for key, flight1 in flights1_dict.items():
        if key not in flights2_dict:
            removed.append(flight1)

    return {
        "added": added,
        "removed": removed,
        "modified": modified
    }

# Вспомогательные функции
def calculate_segment_duration(segment):
    dep_time = datetime.strptime(segment["departure_time"], "%Y-%m-%dT%H%M")
    arr_time = datetime.strptime(segment["arrival_time"], "%Y-%m-%dT%H%M")
    return int((arr_time - dep_time).total_seconds())

def format_duration(total_seconds):
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h {minutes}m"


def parse_xml(file_path):
    flights = []

    tree = ET.parse(file_path)
    root = tree.getroot()

    for itinerary in root.findall(".//Flights"):
        onward_itinerary = itinerary.find("OnwardPricedItinerary/Flights")
        pricing = itinerary.find("Pricing")

        if onward_itinerary is not None and pricing is not None:
            segments = []
            total_price = None

            for charge in pricing.findall("ServiceCharges"):
                if charge.get("type") == "SingleAdult" and charge.get("ChargeType") == "TotalAmount":
                    total_price = float(charge.text)
                    break

            for flight in onward_itinerary.findall("Flight"):
                carrier = flight.find("Carrier").text
                flight_number = flight.find("FlightNumber").text
                source = flight.find("Source").text
                destination = flight.find("Destination").text
                departure_time = flight.find("DepartureTimeStamp").text
                arrival_time = flight.find("ArrivalTimeStamp").text

                duration = calculate_duration(departure_time, arrival_time)

                segments.append({
                    "carrier": carrier,
                    "flight_number": flight_number,
                    "source": source,
                    "destination": destination,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "duration": duration
                })

            flights.append({
                "segments": segments,
                "total_price": total_price
            })

    return flights

def parse_files():
    file1_path = os.path.join(settings.BASE_DIR, 'RS_ViaOW.xml')
    file2_path = os.path.join(settings.BASE_DIR, 'RS_Via-3.xml')

    if not os.path.exists(file1_path) or not os.path.exists(file2_path):
        raise FileNotFoundError("One or both XML files are missing.")

    flights_from_file1 = parse_xml(file1_path)
    flights_from_file2 = parse_xml(file2_path)

    filtered_file1 = filter_flights_by_route(flights_from_file1, "DXB", "BKK")
    filtered_file2 = filter_flights_by_route(flights_from_file2, "DXB", "BKK")

    return filtered_file1, filtered_file2


def calculate_duration(departure, arrival):
    dep_time = datetime.strptime(departure, "%Y-%m-%dT%H%M")
    arr_time = datetime.strptime(arrival, "%Y-%m-%dT%H%M")
    duration = arr_time - dep_time
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes = remainder // 60
    return f'{int(hours)}h {int(minutes)}m'