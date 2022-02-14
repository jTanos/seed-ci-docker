#!/usr/bin/sudo python3
# -*- coding: utf-8 -*-

# Main Controller
import time
import argparse
from datetime import datetime
from multiprocessing import Process, Queue
from typing import List
from stopit import ThreadingTimeout as Timeout
import constants
from repositories.database import DataBase
from controllers.handlers.loghandler import LogHandler
from models.enums import *
from decorators import do_trace
from controllers.handlers.plchandler import PlcHandler, ResultRegister
from controllers.handlers.loghandler import LogHandler
from controllers.handlers.threadhandler import ThreadHandler
from controllers.handlers.processhandler import ProcessHandler, Queue
import multiprocessing
from functools import partial #para pasar los parametros a las funciones


# class CtrlSewingMachine(metaclass=SingletonModel):
class CtrlSewingMachine():
    '''
    Instancia Singleton de manejador de peticiones al PLC de la cosedora.
    '''

    def __init__(self, host:str=constants.PLC_SEWINGMACHINE_A_HOST, weigher_host:str=constants.PLC_WEIGHER_HOST):
        self.host = host
        self.weigher_plc_host = weigher_host
        self.nameSewingMachine = "A" if host == constants.PLC_SEWINGMACHINE_A_HOST else "B"
        self.bags = Queue()
    
    def get_multiple_holding_registers(self, regs:list(SewingMachineSetRegister)) -> List[ResultRegister]:
        return PlcHandler(self.host).read_multiple_holding_register(regs)
    
    def get_register(self, reg:SewingMachineSetRegister) -> ResultRegister:
        return PlcHandler(self.host).read_register(reg)

    def set_register(self, reg:SewingMachineSetRegister, value:bool=False) -> ResultRegister:
        return PlcHandler(self.host).write_register(reg)

    def check_plc_connection(self):
        '''
        Verifica que el plc este funcionando tomando la lectura del spaun.	
        '''
        result = False
        try:
            PlcHandler(self.host).read_register(SewingMachineGetRegister.IO_SPAUN)
            result = True
        except Exception as e:
            result = False
        finally:
            return result

    def get_pressure(self):
        """
        Obtiene la presion leida por el spaun en bar.
        """
        SPAUN_CONVERSION = 16383
        result_bar = 0
        try:
            reg = PlcHandler(self.host).read_register(SewingMachineGetRegister.IO_SPAUN)
            result_bar = round(reg.value * 10 / SPAUN_CONVERSION, 2)
        except Exception as e:
            print(e)
            result_bar = 0
        finally:
            return result_bar

    def cart(self, outside:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        if outside:
            if not bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_2).value):
                sm_plc_handler.write_register(SewingMachineSetRegister.CART_INDOORS, False)
                sm_plc_handler.write_register(SewingMachineSetRegister.CART_OUTSIDE, True)
                
                with Timeout(6) as tm_out:
                    while bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_2).value) == False:
                        pass
                if tm_out.state == tm_out.TIMED_OUT:
                    raise TimeoutError("Se termino el tiempo para deteccion de sensor inductivo de carro afuera")

                sm_plc_handler.write_register(SewingMachineSetRegister.CART_OUTSIDE, False)               
        else:
            if not bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_1).value):
                sm_plc_handler.write_register(SewingMachineSetRegister.CART_OUTSIDE, False)
                sm_plc_handler.write_register(SewingMachineSetRegister.CART_INDOORS, True)               
                with Timeout(6) as tm_out:
                    while bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_1).value) == False:
                        pass
                if tm_out.state == tm_out.TIMED_OUT:
                    raise TimeoutError("Se termino el tiempo para deteccion de sensor inductivo de carro adentro")
                
                sm_plc_handler.write_register(SewingMachineSetRegister.CART_INDOORS, False) 
    
    def is_cart_indoors(self):
        sm_plc_handler = PlcHandler(self.host)
        return bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_1).value)

    def is_cart_outside(self):
        sm_plc_handler = PlcHandler(self.host)
        return bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_2).value)
    
    def open_close_belts(self, close:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_BELTS, close)

    def open_close_arm(self, close:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_ARM, close)

    def on_off_belts(self, on:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        sm_plc_handler.write_register(SewingMachineSetRegister.BELTS_ON_OFF, on)

    def on_off_shorttape(self, on:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_SHORT_ON_OFF, on)
    
    def on_off_longtape(self, on:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_LONG_ON_OFF, on)

    def on_off_sewing(self, on:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        sm_plc_handler.write_register(SewingMachineSetRegister.SEWING, on)

    def cut_thread(self, active:bool=False, **kwargs):
        sm_plc_handler = PlcHandler(self.host)
        sm_plc_handler.write_register(SewingMachineSetRegister.THREAD_CUT, active)       

    def start(self):
        queueCartIndors = Queue()
        queueCartOutside = Queue()
        queueSewingProcess1 = Queue()
        queueSewingProcess2 = Queue()
        queueSewingProcess3 = Queue()

        ProcessHandler().init(nameProcess="CartIndoors", target=cart_move, args=(self.host, False, queueCartIndors))
        ProcessHandler().init(nameProcess="CartOutside", target=cart_move, args=(self.host, True, queueCartOutside))
        ProcessHandler().init(nameProcess="SewingProcess_1", target=sewing_process, args=(self.host, self.bags, queueSewingProcess1))
        ProcessHandler().init(nameProcess="SewingProcess_2", target=sewing_process, args=(self.host, self.bags, queueSewingProcess2))
        ProcessHandler().init(nameProcess="SewingProcess_3", target=sewing_process, args=(self.host, self.bags, queueSewingProcess3))

        sm_plc_handler = PlcHandler(self.host)
        weigher_plc_handler = PlcHandler(self.weigher_plc_host)

        LogHandler.getCurrentClassLogger().debug("INICIO CONFIGURACIONES POR DEFAULT")       
        self.reset()		
        queueCartIndors.put(True)

        # Control para saber que processo ejecutar
        numberSewingProcessRun = 1 

        while True:
            try:
                LogHandler.getCurrentClassLogger().debug("ESPERANDO QUE SE AGARRE LA BOLSA")            
                while bool(weigher_plc_handler.read_holding_register(WeigherSetRegister["HOLD_BAG_" + self.nameSewingMachine.upper()]).value) == False:
                    time.sleep(0.1)

                # Verifico que el brazo este adentro.			
                with Timeout(5) as tm_out:
                    while bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_1).value) == False:
                        pass
                if tm_out.state == tm_out.TIMED_OUT:
                    raise TimeoutError("El carro no se encuentra adentro.")

                self.bags.put(True)

                LogHandler.getCurrentClassLogger().debug("CARRO HACIA BOLSA " + str(datetime.now().time()))
                queueCartOutside.put(True)

                # Leo el sujeta bolsa, cuando la suelta cierro el brazo
                while bool(weigher_plc_handler.read_holding_register(WeigherSetRegister["HOLD_BAG_" + self.nameSewingMachine.upper()]).value) == False:
                    pass

                while bool(weigher_plc_handler.read_holding_register(WeigherSetRegister["HOLD_BAG_" + self.nameSewingMachine.upper()]).value) == True:
                    pass

                LogHandler.getCurrentClassLogger().debug("CIERRO BRAZO")
                sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_ARM, True)

                LogHandler.getCurrentClassLogger().debug("ABRE CORREAS")
                sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_BELTS, False)            

                LogHandler.getCurrentClassLogger().debug("CARRO HACIA ADENTRO")
                queueCartIndors.put(True)
            
                time.sleep(0.3)
                LogHandler.getCurrentClassLogger().debug("ENCIENDO CINTA CORTA")
                sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_SHORT_ON_OFF, True)

                # Process SewingMachine
                if numberSewingProcessRun == 1:
                    numberSewingProcessRun = 2
                    queueSewingProcess1.put(True)
                elif numberSewingProcessRun == 2:
                    numberSewingProcessRun = 3
                    queueSewingProcess2.put(True)
                elif numberSewingProcessRun == 3:
                    numberSewingProcessRun = 1
                    queueSewingProcess3.put(True)
            except Exception as e:
                self.__error(self.nameSewingMachine, e)


    def reset(self):
        sm_plc_handler = PlcHandler(self.host)
        commands = list()
        commands.append(SewingMachineSetRegister.TAPE_LONG_ON_OFF)
        commands.append(SewingMachineSetRegister.TAPE_SHORT_ON_OFF)
        commands.append(SewingMachineSetRegister.BELTS_ON_OFF)
        commands.append(SewingMachineSetRegister.SEWING)
        commands.append(SewingMachineSetRegister.THREAD_CUT) 
        commands.append(SewingMachineSetRegister.CLOSE_BELTS) 
        commands.append(SewingMachineSetRegister.CLOSE_ARM) 
        sm_plc_handler.write_multiple_registers(commands, False)

    def __error(self, nameSewingMachine, exception, *args):
        if nameSewingMachine == "A":
            DataBase().setError(ErrorEnum.SEWINGMACHINE_A_NOTFOUND)
        else:
            DataBase().setError(ErrorEnum.SEWINGMACHINE_B_NOTFOUND)

        LogHandler.getCurrentClassLogger().exception("Check Errors. %s", exception)
                      

def cart_move(host:str='', outside:bool=True, queue=None, **kwargs):
    LogHandler.setLogHandlers(DataBase().getSettings(forceupdate=True))
    sm_plc_handler = PlcHandler(host)
    nameSewingMachine = "A" if host == constants.PLC_SEWINGMACHINE_A_HOST else "B"

    LogHandler.getCurrentClassLogger().debug("INIT CART MOVE " + ("OUTSIDE " if outside else "INDORS ") + str(datetime.now().time()))
    while True:
        queue.get()
        try:
            LogHandler.getCurrentClassLogger().debug("START CART MOVE " + ("OUTSIDE " if outside else "INDORS ") + str(datetime.now().time()))
            if outside:
                if not bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_2).value):
                    sm_plc_handler.write_register(SewingMachineSetRegister.CART_INDOORS, False)
                    sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_ARM, False)
                    sm_plc_handler.write_register(SewingMachineSetRegister.CART_OUTSIDE, True)
                    
                    with Timeout(5) as tm_out:
                        while bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_2).value) == False:
                            pass

                    LogHandler.getCurrentClassLogger().debug("CARRO AFUERA")
                    sm_plc_handler.write_register(SewingMachineSetRegister.CART_OUTSIDE, False)
                    if tm_out.state == tm_out.TIMED_OUT:
                        raise TimeoutError("Se termino el tiempo para deteccion de sensor inductivo de carro afuera")
            else:
                if not bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_1).value):
                    sm_plc_handler.write_register(SewingMachineSetRegister.CART_OUTSIDE, False)
                    # time.sleep(0.1)
                    sm_plc_handler.write_register(SewingMachineSetRegister.CART_INDOORS, True)

                    with Timeout(5) as tm_out:
                        while bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_INDUCTIVO_1).value) == False:
                            pass
                    
                    sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_ARM, False)
                    time.sleep(0.1)
                    sm_plc_handler.write_register(SewingMachineSetRegister.CART_INDOORS, False)
                    
                    if tm_out.state == tm_out.TIMED_OUT:
                        raise TimeoutError("Se termino el tiempo para deteccion de sensor inductivo de carro adentro")
                
                time.sleep(0.5)
                sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_SHORT_ON_OFF, False)
                LogHandler.getCurrentClassLogger().debug("CARRO ADENTRO Y ABIERTO")
        except Exception as e:
            DataBase().setError(ErrorEnum.SEWINGMACHINE_A_NOTFOUND if nameSewingMachine == "A" else ErrorEnum.SEWINGMACHINE_B_NOTFOUND)
            LogHandler.getCurrentClassLogger().exception("cart_move sewing %s. %s" % (nameSewingMachine, e))

def sewing_process(host:str, bags:Queue, queue=None, **kwargs):
    settings_sewing_machine = DataBase().getSewingMahcineSettings() 
    LogHandler.setLogHandlers(DataBase().getSettings(forceupdate=True))
    sm_plc_handler = PlcHandler(host)
    nameSewingMachine = "A" if host == constants.PLC_SEWINGMACHINE_A_HOST else "B"

    LogHandler.getCurrentClassLogger().debug("INIT SEWING PROCESS " + str(datetime.now().time()))
    while True:
        queue.get()
        try:
            LogHandler.getCurrentClassLogger().debug("ENCIENDO CINTA LARGA Y CORREAS")
            sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_LONG_ON_OFF, True)
            sm_plc_handler.write_register(SewingMachineSetRegister.BELTS_ON_OFF, True)
            
            time.sleep(0.5)
            LogHandler.getCurrentClassLogger().debug("CIERRA CORREAS")
            sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_BELTS, True)

            with Timeout(8) as tm_out:
                while bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_OPTICO).value) == False:
                    pass
            if tm_out.state == tm_out.TIMED_OUT:                
                raise TimeoutError("Se termino el tiempo de espera de entrada de bolsa en sensor optico")

            # Tiempo despues de detectar el sensor para encender la cosedora
            time.sleep(settings_sewing_machine.TimeInSecondsBeforeStartingToSew)

            LogHandler.getCurrentClassLogger().debug("ENCIENDO COSEDORA")
            sm_plc_handler.write_register(SewingMachineSetRegister.SEWING, True)
            
            # Tiempo minimo de funcionamiento de cosedora
            time.sleep(settings_sewing_machine.MinimumOperatingTimeInSeconds)

            with Timeout(5) as tm_out:
                while bool(sm_plc_handler.read_register(SewingMachineGetRegister.SENSOR_OPTICO).value) == True:
                    pass
            if tm_out.state == tm_out.TIMED_OUT:
                raise TimeoutError("Se termino el tiempo de espera de salida de bolsa del sensor optico")

            # Timpo despues de dejar de detectar el sensor para cortar el hilo
            time.sleep(settings_sewing_machine.TimeInSecondsAfterSewing)
            
            LogHandler.getCurrentClassLogger().debug("ACTIVO CORTAR HILO")
            sm_plc_handler.write_register(SewingMachineSetRegister.THREAD_CUT, True)
            time.sleep(0.1)
            LogHandler.getCurrentClassLogger().debug("APAGO COSEDORA")
            sm_plc_handler.write_register(SewingMachineSetRegister.SEWING, False)
            time.sleep(0.4)
            LogHandler.getCurrentClassLogger().debug("DESACTIVO CORTAR HILO")
            sm_plc_handler.write_register(SewingMachineSetRegister.THREAD_CUT, False)

            ThreadHandler().init(nameThread="IncreaseSewingMachine", target=partial(DataBase().setBagInSewingMahcine, True if nameSewingMachine == "A" else False))
            
            bags.get_nowait()
            time.sleep(2)
            if bags.empty():
                LogHandler.getCurrentClassLogger().debug("APAGO CINTA LARGA Y CORREAS")
                sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_LONG_ON_OFF, False)
                sm_plc_handler.write_register(SewingMachineSetRegister.BELTS_ON_OFF, False)
        except Exception as e:
            bags.get_nowait()
            sm_plc_handler.write_register(SewingMachineSetRegister.SEWING, False)
            sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_LONG_ON_OFF, False)
            sm_plc_handler.write_register(SewingMachineSetRegister.TAPE_SHORT_ON_OFF, False)
            sm_plc_handler.write_register(SewingMachineSetRegister.BELTS_ON_OFF, False)
            sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_ARM, False)
            sm_plc_handler.write_register(SewingMachineSetRegister.CLOSE_BELTS, False)
            sm_plc_handler.write_register(SewingMachineSetRegister.CART_INDOORS, True)

            DataBase().setError(ErrorEnum.SEWINGMACHINE_A_NOTFOUND if nameSewingMachine == "A" else ErrorEnum.SEWINGMACHINE_B_NOTFOUND)
            LogHandler.getCurrentClassLogger().exception("sewing_process sewing %s. %s" % (nameSewingMachine, e))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    ctrl_self = None
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', type=str, default=constants.PLC_SEWINGMACHINE_A_HOST, help='ip for sewing machine')
        parser.add_argument('--weigher-host', type=str, default=constants.PLC_WEIGHER_HOST, help='ip for weigher machine')	
        opt = parser.parse_args()

        LogHandler.setLogHandlers(DataBase().getSettings(forceupdate=True))
        ctrl_self = CtrlSewingMachine(host= opt.host, weigher_host= opt.weigher_host)
        ctrl_self.start()  
    except Exception as e:
        LogHandler.getCurrentClassLogger().exception("Error en init Cosedora %s. %s" % (opt.host, e))       
        if opt.host == constants.PLC_SEWINGMACHINE_A_HOST:
            DataBase().setError(ErrorEnum.SEWINGMACHINE_A_NOTFOUND)
        else:
            DataBase().setError(ErrorEnum.SEWINGMACHINE_B_NOTFOUND)
    finally:
        ProcessHandler().kill_all()
        ThreadHandler().stop_all()
        if ctrl_self is not None:
            ctrl_self.reset()       