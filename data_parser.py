import xml.etree.ElementTree as ET
import math


def parse(name):
    tree = ET.parse(name)
    root = tree.getroot()

    #helpful variables
    dist = {}
    time = {}
    main_city_index = -1
    pallets = {}
    vehicles_pallets = {}
    pallet_to_std_ratio = 0

    # output variables
    locations = {}
    travel_times = {}
    demands_pal = []
    demands_kg = []
    start_times = []
    end_times = []
    vehicles_pal = []
    vehicles_kg = []
    vehicles_cost = []
    vehicles_maxkm = []

    # location indexes array ---------------------------
    locIds = [0] * len(root[0])
    for loc in root[0]:
        locIds[int(loc.attrib['idx'])] = loc.attrib['id']

    # locations parse ----------------------------------
    for i in range(len(root[0])):
        dist[i] = {}
        time[i] = {}
        for j in range(len(root[0])):
            dist[i][j] = 0
            time[i][j] = 0

    for loc in root[0]:
        if(loc.attrib['is_DC']) == 'true':
            main_city_index = int(loc.attrib['idx'])
        for distance in loc.find('Travel_Data'):
            dist[int(loc.attrib['idx'])][int(distance.attrib['location_idx'])] = float(distance.attrib['kms']) * 1000
            time[int(loc.attrib['idx'])][int(distance.attrib['location_idx'])] = float(distance.attrib['time'])

    # pallets parse --------------------------
    for i in range(len(root[2])):
        pallets[i] = 0

    for pall in root[2]:
        pallets[int(pall.attrib['idx'])] = float(pall.attrib['ratio_to_stdPallet']) * 100

    # orders ---------------------------------------------
    for i in range(len(root[1]) + 1):
        locations[i] = {}
        for j in range(len(root[1]) + 1):
            locations[i][j] = 0

    # first row of locations ( for depo )
    for order in root[1]:
        locations[0][int(order.attrib['idx']) + 1] = dist[main_city_index][locIds.index(order.attrib['location_to'])]
        locations[int(order.attrib['idx']) + 1][0] = dist[locIds.index(order.attrib['location_to'])][main_city_index]

    # rest
    for order in root[1]:
        index_from = locIds.index(order.attrib['location_to'])
        for order_to in root[1]:
            index_to = locIds.index(order_to.attrib['location_to'])
            locations[int(order.attrib['idx']) + 1][int(order_to.attrib['idx']) + 1] = dist[index_from][index_to]

    # travel_times ---------------------------------------
    for i in range(len(root[1]) + 1):
        travel_times[i] = {}
        for j in range(len(root[1]) + 1):
            travel_times[i][j] = 0

    # first row of travel_times ( for depo )
    for order in root[1]:
        travel_times[0][int(order.attrib['idx']) + 1] = time[main_city_index][locIds.index(order.attrib['location_to'])]
        travel_times[int(order.attrib['idx']) + 1][0] = time[locIds.index(order.attrib['location_to'])][main_city_index]

    # rest
    for order in root[1]:
        index_from = locIds.index(order.attrib['location_to'])
        for order_to in root[1]:
            index_to = locIds.index(order_to.attrib['location_to'])
            travel_times[int(order.attrib['idx']) + 1][int(order_to.attrib['idx']) + 1] = time[index_from][index_to]

    # demands_pal && demands_kg ------------------------
    demands_pal.append(0)
    demands_kg.append(0)
    for order in root[1]:
        demands_pal.append(int(order.attrib['pallet_quantity']) * pallets[int(order.attrib['pallet_type_idx'])])
        demands_kg.append(int(order.attrib['weight_per_pallet']) * int(order.attrib['pallet_quantity']))

    # start_times && end_times ------------------------
    start_times.append(0)
    end_times.append(0)
    for order in root[1]:
        start_times.append(int(order.attrib['delivery_start']))
        end_times.append(int(order.attrib['delivery_end']))

    # pallets ------------------------------------------
    pallet_to_std_ratio = float(root[2].find('Pallet').attrib['ratio_to_stdPallet'])

    # fleets (cars) ------------------------------------
    for car in root[3]:
        index = int(car.attrib['idx'])
        vehicles_pal.append(math.floor(int(car.find('Loading_Sections').find('Section').attrib['capacity_in_stdPallets']) * 100))
        vehicles_kg.append(int(car.attrib['max_weight']))
        vehicles_cost.append(float(car.attrib['cost_per_km']))
        vehicles_maxkm.append(int(car.attrib['max_kms']) * 1000)

    # print to console ---------------------------------



    # if True:
    # # if False:
    #     print("Location big ids:", locIds)
    #     print("Main city index:", main_city_index)
    #     print("\nDistances:", dist)
    #     print("\nTimes:", time)
    #     #print("\nLocations:", locations)
    #     #print("\nTravel times:", travel_times)
    #     print("\ndemans_pal", demands_pal)
    #     print("\ndemands_kg", demands_kg)
    #     print("\nstart_times", start_times)
    #     print("\nend_times", end_times)
    #     print("\nFirst pallet ratio:", pallet_to_std_ratio)
    #     print("\nvehicles_pal:", vehicles_pal)
    #     print("\nvehicles_kg:", vehicles_kg)
    #     print("\nvehicles_cost:", vehicles_cost)
    #     print("\nvehicles_maxkm:", vehicles_maxkm)
    data = [locations, travel_times, demands_pal, demands_kg, start_times, end_times, vehicles_pal, vehicles_kg,
            vehicles_cost, vehicles_maxkm]
    return data

