import math
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import data_parser


# Cost callback
class CreateCostCallback(object):
    """Create callback to calculate cost and travel times between points."""

    def __init__(self, locations, vehicle_cost_per_km):
        """Initialize distance array."""
        num_locations = len(locations)
        self.matrix = {}

        for from_node in range(num_locations):
            self.matrix[from_node] = {}
            for to_node in range(num_locations):
                self.matrix[from_node][to_node] = locations[from_node][to_node] * vehicle_cost_per_km

    def Cost(self, from_node, to_node):
        return self.matrix[from_node][to_node]

# Demand callback
class CreateDemandPalCallback(object):
    """Create callback to get demands at location node."""

    def __init__(self, demands_pal):
        self.matrix = demands_pal

    def DemandPal(self, from_node, to_node):
        return self.matrix[from_node]

# Demand callback
class CreateDemandKgCallback(object):
    """Create callback to get demands at location node."""

    def __init__(self, demands_kg):
        self.matrix = demands_kg

    def DemandKg(self, from_node, to_node):
        return self.matrix[from_node]


# Create the travel time callback.
class CreateTravelTimeCallback(object):
    """Create callback to get travel times between locations."""

    def __init__(self, travel_times):
        self.travel_times = travel_times

    def TravelTime(self, from_node, to_node):
        return self.travel_times[from_node][to_node]


def do_everything(file_name, firsto_solutiono_strategeiro, go_back_to_depo=True):
    # Create the data.
    # data = create_data_array()
    data = data_parser.parse(file_name)
    locations = data[0]
    travel_times = data[1]

    demands_pal = data[2]
    demands_kg = data[3]

    start_times = data[4]
    end_times = data[5]

    vehicles_pal = data[6]
    vehicles_kg = data[7]
    vehicles_cost = data[8]
    vehicles_maxkm = data[9]

    multi_start = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    multi_end = [0, 1, 18, 50, 0, 0, 1, 18, 50, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 1, 18, 50, 0]

    num_locations = len(locations)
    num_vehicles = len(vehicles_pal)
    depot = 0
    search_time_limit_ms = 300000
    local_search_max_time_ms = 3000

    # Result variables
    result = []
    tmp_route = []
    h_route_dist = 0
    h_route_time = 0
    tmp_orders = []

    # Create routing model.
    if num_locations > 0:

        # The number of nodes of the VRP is num_locations.
        # Nodes are indexed from 0 to num_locations - 1. By default the start of
        # a route is node 0.
        if go_back_to_depo:
            routing = pywrapcp.RoutingModel(num_locations, num_vehicles, depot)
        else:
            routing = pywrapcp.RoutingModel(num_locations, num_vehicles, multi_start, multi_end)
        search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
        search_parameters.first_solution_strategy = firsto_solutiono_strategeiro
        search_parameters.time_limit_ms = search_time_limit_ms
        search_parameters.lns_time_limit_ms = local_search_max_time_ms
        # print(search_parameters)


        ############################# Callbacks to the distance function and travel time functions here.
        cost_callback_matrix = []
        for v_id in range(len(vehicles_cost)):
            cost_between_locations = CreateCostCallback(locations, vehicles_cost[v_id])
            cost_callback = cost_between_locations.Cost
            cost_callback_matrix.append(cost_callback)
            routing.SetArcCostEvaluatorOfVehicle(cost_callback, v_id)


        ############################# Adding pallets dimension constraints.
        demands_pal_at_orders = CreateDemandPalCallback(demands_pal)
        demands_pal_callback = demands_pal_at_orders.DemandPal

        NullCapacitySlack = 0;
        fix_start_cumul_to_zero = True
        pallets = "Pallets"

        routing.AddDimensionWithVehicleCapacity(demands_pal_callback, NullCapacitySlack, vehicles_pal, fix_start_cumul_to_zero, pallets)

        ############################# Adding weight dimension constraints.
        demands_kg_at_orders = CreateDemandKgCallback(demands_kg)
        demands_kg_callback = demands_kg_at_orders.DemandKg

        NullCapacitySlack = 0;
        fix_start_cumul_to_zero = True
        kilograms = "Kilograms"

        routing.AddDimensionWithVehicleCapacity(demands_kg_callback, NullCapacitySlack, vehicles_kg, fix_start_cumul_to_zero, kilograms)

        ############################# Adding kmlimit dimension constraints.
        demands_kms_at_orders = CreateCostCallback(locations, 1)
        demands_kms_callback = demands_kms_at_orders.Cost

        NullCapacitySlack = 0;
        fix_start_cumul_to_zero = True
        kilometers = "Kilometers"

        routing.AddDimensionWithVehicleCapacity(demands_kms_callback, NullCapacitySlack, vehicles_maxkm, fix_start_cumul_to_zero, kilometers)

        ############################## Add time dimension.
        day = max(end_times)
        time = "Time"

        travelllo_times = CreateTravelTimeCallback(travel_times)
        travel_time_callback = travelllo_times.TravelTime

        routing.AddDimension(travel_time_callback, day, day, fix_start_cumul_to_zero, time)


        ############################# Add time window constraints.
        time_dimension = routing.GetDimensionOrDie(time)
        for location in range(1, num_locations):
            start = start_times[location]
            end = end_times[location]
            time_dimension.CumulVar(location).SetRange(start, end)

        ############################ Solve displays a solution if any.
        assignment = routing.SolveWithParameters(search_parameters)
        if assignment:
            size = len(locations)
            # Solution cost.
            # print("Total cost of all routes: " + str(assignment.ObjectiveValue()/1000) + "\n")
            result.append(assignment.ObjectiveValue()/1000)
            result.append(0)
            # Inspect solution.
            pallets_dimension = routing.GetDimensionOrDie(pallets)
            kilograms_dimension = routing.GetDimensionOrDie(kilograms)
            kilometers_dimension = routing.GetDimensionOrDie(kilometers)
            time_dimension = routing.GetDimensionOrDie(time)

            for vehicle_nbr in range(num_vehicles):
                index = routing.Start(vehicle_nbr)
                # plan_output = 'Vehicle {0}:'.format(vehicle_nbr)

                while not routing.IsEnd(index):
                    node_index = routing.IndexToNode(index)
                    time_var = time_dimension.CumulVar(index)
                    tmp_orders.append([node_index-1, assignment.Min(time_var), assignment.Max(time_var)])
                    kilometers_var = kilometers_dimension.CumulVar(index)
                    time_var = time_dimension.CumulVar(index)
                    h_route_dist = assignment.Value(kilometers_var) / 1000
                    h_route_time = assignment.Min(time_var)
                    # plan_output += " Order {node_index} Time({tmin}, {tmax}) -> ".format(
                    #                 node_index=node_index,
                    #                 tmin=str(assignment.Min(time_var)),
                    #                 tmax=str(assignment.Max(time_var)))
                    index = assignment.Value(routing.NextVar(index))

                node_index = routing.IndexToNode(index)
                pallets_var = pallets_dimension.CumulVar(index)
                kilograms_var = kilograms_dimension.CumulVar(index)
                kilometers_var = kilometers_dimension.CumulVar(index)
                time_var = time_dimension.CumulVar(index)

                # plan_output += " {node_index} Load({load}) Time({tmin}, {tmax})".format(
                #                 node_index=node_index,
                #                 load=assignment.Value(load_var),
                #                 tmin=str(assignment.Min(time_var)),
                #                 tmax=str(assignment.Max(time_var)))
                # print(plan_output)
                # print("\n")

                tmp_orders.append([node_index-1, assignment.Min(time_var), assignment.Max(time_var)])

                tmp_route.append(vehicle_nbr)

                tmp_route.append(assignment.Value(kilometers_var) / 1000 * vehicles_cost[vehicle_nbr])
                tmp_route.append(assignment.Value(kilometers_var) / 1000)
                tmp_route.append(assignment.Min(time_var))

                result[1] += h_route_dist * vehicles_cost[vehicle_nbr]

                tmp_route.append(h_route_dist * vehicles_cost[vehicle_nbr])
                tmp_route.append(h_route_dist)
                tmp_route.append(h_route_time)

                tmp_route.append(assignment.Value(pallets_var)/100)
                tmp_route.append(vehicles_pal[vehicle_nbr]/100)
                tmp_route.append(assignment.Value(pallets_var) / vehicles_pal[vehicle_nbr])

                tmp_route.append(assignment.Value(kilograms_var))
                tmp_route.append(vehicles_kg[vehicle_nbr])
                tmp_route.append(assignment.Value(kilograms_var) / vehicles_kg[vehicle_nbr])

                tmp_route.append(tmp_orders)

                if len(tmp_orders) > 2:
                    result.append(tmp_route)

                tmp_orders = []
                tmp_route = []

            return result

        else:
            print(str(firsto_solutiono_strategeiro)+' No solution found.')
            return [float('inf')]
    else:
        print('Specify an instance greater than 0.')



def create_data_array():

    locations = [[0, 326550, 326550, 316050], [327600, 0, 0, 17955], [327600, 0, 0, 17955], [318150, 17850, 17850, 0]]

    travel_times = [[0, 174, 174, 167], [175, 0, 0, 39], [175, 0, 0, 39], [170, 39, 39, 0]]

    demands_pal = [0, 1, 1, 1]
    demands_kg = [0, 100, 100, 100]

    start_times =  [0, 0, 0, 0]
    end_times = [1440, 1440, 1440, 1440]

    vehicles_pal = [15, 3, 20]
    vehicles_kg = [8700, 1300, 10300]
    vehicles_cost = [2.45, 1.4, 3]
    vehicles_maxkm = [1000, 1000, 1000]

    data = [locations, travel_times, demands_pal, demands_kg, start_times, end_times, vehicles_pal, vehicles_kg, vehicles_cost, vehicles_maxkm]

    return data

def present_result(result):
    print("Total cost of all routes: " + str(result[0]))
    print("Total cost of all routes without return to DC: " + str(round(result[1], 2)))
    print("\n============================================\n")
    it = 0
    for r in result[2:]:
        print("Route number: " + str(it) + "        Vehicle: " + str(r[0]) +"\n")
        print("Full route cost: " + str(round(r[1], 2)))
        print("Full route distance: " + str(round(r[2], 2)) + " [Km]")
        print("Full route time: " + str(r[3]) + " [Min]\n")

        print("Route cost without return to DC: " + str(round(r[4], 2)))
        print("Route distance without return to DC: " + str(round(r[5], 2)) + " [Km]")
        print("Route time without return to DC: " + str(r[6]) + " [Min]\n")

        print("Vehicle space used: " + str(r[7]) + "/" + str(r[8]) + " [Std Pallets]")
        print("Vehicle space utilization: " + str(round(r[9]*100, 2)) + "%\n")

        print("Vehicle max weight used: " + str(r[10]) + "/" + str(r[11]) + " [Kg]")
        print("Vehicle max weight utilization: " + str(round(r[12]*100, 2)) + "%\n")

        print("Realize orders:")
        for o in r[13]:
            if o[0] == -1:
                print(" DC: leave_time: " + str(o[1]) + " max_leave_time: " + str(o[2]))
            else:
                print("%03d: leave_time: "% o[0] + str(o[1]) + " max_leave_time: " + str(o[2]))
        print("\n============================================\n")
        it += 1

def main():
    file_name = 'ziwl_data_6.xml'
    go_back_to_depo = True
    res = []
    res.append(do_everything(file_name, routing_enums_pb2.FirstSolutionStrategy.SAVINGS, go_back_to_depo))
    # res.append(do_everything(file_name, routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC, go_back_to_depo))
    res.append(do_everything(file_name, routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC, go_back_to_depo))

    min = res[0][0]
    for sol in res:
        if sol[0] < min:
            min = sol[0]

    for sol in res:
        if sol[0] == min:
            present_result(sol)

if __name__ == '__main__':
    main()
