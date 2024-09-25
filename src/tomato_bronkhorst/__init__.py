from tomato.driverinterface_1_0 import ModelInterface, Attr, Task
from propar import PP_TYPE_FLOAT, instrument as Instrument
from typing import Any

#eventually replace 'param_id' by 'dde_nr ' ? it works so far but since we add new parameters 
#I am afraid that we encounter some conflicts since we have the same dde numbers for the devices . 
#updated property maps, I added what you asked, in the questions I 
property_map = {
    'temperature': {'proc_nr': 33, 'parm_nr': 7},
    'flow': {'param_id': 205},
    'fluid_name' :{'param_id' : 25},
    'fluid_unit':{'param_id' : 129},
    'pressure': {'param_id': 205},
    'max_flow': {'param_id': 128},
    'flow_unit': {'param_id': 129},
    'device_number' : {'param_id' : 90 },
    'firmware_version' : {'param_id' : 105}, 
    'serial_number' : {'param_id' : 92},
    'capacity_flow' : {'param_id' : 21}, 
    'identification_number_press' : {'param_id' : 175}, 
    'pressure_sensor_type' : {'param_id' : 22},
    
    
}

#suggestions : fn internal to to the class : single _ method : Done (if I understood it correctly : 
#it is signaling that it’s likely used by other methods in DeviceManager but isn’t meant to be called directly from outside the class 
#but on this I am not sure. 

class DriverInterface(ModelInterface):
    class DeviceManager(ModelInterface.DeviceManager):
        instrument: Instrument

        def __init__(self, driver: ModelInterface, key: tuple[str, int], **kwargs: dict):
            super().__init__(driver, key, **kwargs)
            address, channel = key
            self.instrument = Instrument(comport=address, address=channel)
            
            # Determine device type
            self.device_type = self.determine_device_type()
            
            # Store device information
            self.serial_number = self.instrument.readParameter(1, 92)
            self.flow_units = self.get_flow_units()
            self.pressure_units = self.get_pressure_units()

        def _determine_device_type(self):
            device_type = self.instrument.readParameter(1, 72)
            return "MFC" if device_type == 90 else "PC" if device_type == 91 else "Unknown"
#checked with pint ! 


#I took your remark into account and raised an error instead
#IT HAS BEEN VERIFIED WITH PINT 
       def _get_flow_units(self):
        flow_unit_id = self.instrument.readParameter(129)
        unit_map = {
            1: "mg/h", 2: "g/h", 3: "kg/h", 4: "g/s", 5: "ml/min",
            6: "l/min", 7: "l/h", 8: "mg/min", 9: "g/min", 10: "kg/min",
            11: "lb/h"
            }
    
    if flow_unit_id not in unit_map:
        raise ValueError(f"Unknown flow unit ID: {flow_unit_id}")
    
    return unit_map[flow_unit_id] 
        #cntp to check 

        def _get_pressure_units(self):
    pressure_unit_id = self.instrument.readParameter(130)
    unit_map = {
        0: "bar", 1: "psi", 2: "Pa", 3: "kPa", 4: "torr",
        5: "atm", 6: "mbar", 7: "mH2O", 8: "kg/cm2"
    }
    
    if pressure_unit_id not in unit_map:
        raise ValueError(f"Unknown pressure unit ID: {pressure_unit_id}")
    
    return unit_map[pressure_unit_id]

        #raise an exception for errors .-> crashes with a good error message 



# with or without the _ ? the do_task, untouched
    def do_task(self, task: Task, **kwargs):
        pass 
    #I do not touch it, supposed to update every elements of the dictionnary.

#am I supposed to put a "_" ON THIS ONE ?
# we could change there and have a input /output for the number of device we want to connect 
def _list_available_devices():
    print("\nSearching for available devices...")
    available_ports = []
    for i in range(256):  # I doubt we will need as much 
        port = f"COM{i}"
        try:
            instrument = propar.instrument(port)
            nodes = instrument.master.get_nodes()
            if nodes:
                available_ports.append((port, nodes))
        except Exception:
            pass  #used for testing in case we do not have access to the lab
    
    if not available_ports:
        print("No devices found.")
    else:
        print("\nAvailable Devices:")
        for i, (port, nodes) in enumerate(available_ports):
            for j, node in enumerate(nodes):
                print(f"{i+1}.{j+1}. Port: {port}, Node: {node}")

#here I added the last element from my tests : 
def _connect_device(self, port):
    self.instrument = self.setup_instrument(port)
    self.nodes = self.instrument.master.get_nodes()
    if not self.nodes:
        print("No devices found on the network.")
    else:
        print("\nAvailable Devices:")
        for i, node in enumerate(self.nodes):
            print(f"{i+1}. {node}")
    
    # Get additional parameters
    self.max_flow_rate = self.read_property('max_flow_rate')
    self.max_flow_unit = self.read_property('flow_unit')
    self.device_number = self.read_property('device_number')
    self.sensor_type = self.read_property('pressure_sensor_type')
    self.id_number_pc = self.read_property('identification_number_press')
    self.firmware_version = self.read_property('firmware_version')
    self.serial_number = self.read_property('serial_number')
    self.capacity_flow = self.read_property('capacity_flow')

    

def _get_valid_port():
    while True:
        port = input("Enter the COM port (e.g., 'COM4'): ")
        if isinstance(port, str):
            return port
        else:
            print("Invalid input. Please enter a valid COM port as a string.")
    
def _get_experiment_duration():
    while True:
        try:
            duration = int(input('Enter the duration of the experiment in seconds: '))
            return duration
        except ValueError:
            print("Invalid input. Please enter an integer value for the duration.")

#as mentionned we can continue to use on th setpoint or the dde number 
def _open_valve_fully(self):
    print("Opening valve fully...")
    self.instrument.setpoint = 100.0

def _close_valve(self):
    print("Closing valve fully...")
    self.instrument.setpoint = 0.0
    

def _collect_data(self, duration):
        temperature_data = []
        flow_rate_data = []
        pressure_data = []
        timestamps = []
        end_time = time.time() + duration
        while time.time() < end_time:
            temperature = self.read_property('temperature')
            flow_rate = self.read_property('flow_rate')
            pressure = self.read_property('pressure')

            temperature_data.append(temperature)
            flow_rate_data.append(flow_rate)
            pressure_data.append(pressure)
            timestamps.append(time.time())
            
            print(
                f"Time: {time.time():.2f} s, "
                f"Temperature: {temperature:.2f} °C, "
                f"Flow Rate: {flow_rate:.2f} {self.max_flow_unit or 'Unknown'}, "
                f"Pressure: {pressure:.2f} bar"
            )

            time.sleep(1)

        self.close_valve()
        temperature_array = xr.DataArray(
            temperature_data,
            coords=[timestamps],
            dims=["time"],
            name="temperature",
            attrs={"units": "°C"}
        )

        flow_rate_array = xr.DataArray(
            flow_rate_data,
            coords=[timestamps],
            dims=["time"],
            name="flow_rate",
            attrs={"units": self.max_flow_unit}
        )
        pressure_array = xr.DataArray(
            pressure_data,
            coords=[timestamps],
            dims=["time"],
            name="pressure",
            attrs={"units": "bar"}
        )
        dataset = xr.Dataset({
            "temperature": temperature_array,
            "flow_rate": flow_rate_array,
            "pressure": pressure_array
        })

        return dataset


    
#IDEA FOR THE ATTRIBUTES : 
# set a loop that determine whether the status is True or False and stop the program if we encounter weird values. 
# 
        def _set_attr(self, attr: str, val: Any, **kwargs: dict):
            if attr in property_map:
                params = property_map[attr]
                if 'param_id' in params:
                    self.instrument.writeParameter(params['param_id'], val)
                else:
                    self.instrument.write_parameters([{**params, 'data': val}])
            else:
                raise ValueError(f"Unknown property: {attr}")

        def _get_attr(self, attr: str, **kwargs: dict):
            if attr in property_map:
                params = property_map[attr]
                if 'param_id' in params:
                    return self.instrument.readParameter(params['param_id'])
                else:
                    values = self.instrument.read_parameters([params])
                    return values[0]['data']
            else:
                raise ValueError(f"Unknown property: {attr}")

        def _attrs(self, **kwargs) -> dict[str, Attr]:
            attrs_dict = {
                'temperature': Attr(type=float, units="Celsius"),
                #as mentionned now, the user can not modify the data, only read them. 
                'flow': Attr(type=float, units=self.flow_units, rw=False, status=True),
                'pressure' :Attr(type=float, units=self.pressure_unit_id, rw=False)
            }
            if self.device_type == "PC":
                attrs_dict['pressure'] = Attr(type=float, units=self.pressure_units, rw=False)
            return attrs_dict

        def _capabilities(self, **kwargs) -> set:
            caps = {"constant_flow"}
            if self.device_type == "PC":
                caps.add("constant_pressure")
            return caps

# I still have to find a way to modify this for the kwargs and adress. 
if __name__ == "__main__":
    kwargs = dict(address="COM4", channel=4)
    interface = DriverInterface()
    print(f"{interface=}")
    print(f"{interface.dev_register(**kwargs)=}")
    print(f"{interface.devmap=}")
    print(f"{interface.dev_get_attr(attr='temperature', **kwargs)=}")
    print(f"{interface.dev_get_attr(attr='flow', **kwargs)=}")
    print(f"{interface.dev_status(**kwargs)=}")