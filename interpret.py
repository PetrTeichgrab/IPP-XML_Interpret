import re
import xml.etree.ElementTree as et
import argparse 

# • 52 - chyba při sémantických kontrolách vstupního kódu v IPPcode23 (např. použití nedefino-
# vaného návěští, redefinice proměnné);
# • 53 - běhová chyba interpretace – špatné typy operandů;
# • 54 - běhová chyba interpretace – přístup k neexistující proměnné (rámec existuje);
# • 55 - běhová chyba interpretace – rámec neexistuje (např. čtení z prázdného zásobníku rámců);
# • 56 - běhová chyba interpretace – chybějící hodnota (v proměnné, na datovém zásobníku nebo
# v zásobníku volání);
# • 57 - běhová chyba interpretace – špatná hodnota operandu (např. dělení nulou, špatná návra-
# tová hodnota instrukce EXIT);
# • 58 - běhová chyba interpretace – chybná práce s řetězcem.

exitCodes = {
    "SemanticCheckError" : 52,
    "FalseOperandTypeError" : 53,
    "NonExistingVariableError" : 54,
    "NonExistingFrameError" : 55,
    "MissingValueError" : 56,
    "FalseOperandValueError" : 57,
    "FalseStringOperationError" : 58
}


class ArgsParser:

    def CreateParser(self):
        self.parser = argparse.ArgumentParser(
        prog='Interpret',
        description='Interpret of XML code')
        return self.parser

    def AddArgs(self):
        self.parser.add_argument('-s', '--source', nargs=1)

    #TODO: def CheckArgs():

    def GetFileName(self):
        arguments = self.parser.parse_args()
        return arguments.source[0]
    
    def GetXmlTree(self):
        return et.parse(self.GetFileName())

    def ProcessArgs(self):
        self.parser = self.CreateParser()
        self.AddArgs()


class Instruction:

    def __init__(self, order:int, opcode:str):
        self._order = order
        self._opcode = opcode
        self._argList = []
    
    def AddArgument(self,arg):
        self._argList.append(arg)

    def GetOrder(self):
        return self._order
    
    def GetOpcode(self):
        return self._opcode
    
    def GetArgs(self):
        return self._args
    

class Frame:
    frame = {}
    def __init__(self) -> None:
        self.globalFrame = {}
        self.localFrame = []
        self.tempFrame = None

    def Add(self,name, value):
        self.frame[name] = value
    
    def Remove(self, name):
        del self.frame[name]

    def CreateFrame(self):
        self.tempFrame = {}

    def PushFrame(self):
        self.localFrame.append(self.tempFrame)
        self.tempFrame = None
    
    def PopFrame(self):
        if bool(self.localFrame):
            exit(exitCodes["NonExistingFrameError"])
        self.tempFrame = self.localFrame[-1]


class ArithmeticInstruction(Instruction):

        def __init__(self, order:int, opcode:str):
            super().__init__(order, opcode)

        def Add(var, sym1, sym2):
            var = sym1 + sym2
            return var
        
        def Sub(var, sym1, sym2):
            var = sym1 + sym2
            return var
        
        def Mul(var, sym1, sym2):
            var = sym1 * sym2
            return var
        
        def Idiv(var, sym1, sym2):
            if not((isinstance(var), int) and (isinstance(sym1,int) and isinstance(sym2), int)):
                exit(exitCodes["FalseOperandValueError"])
            if(sym2 == 0):
                exit(exitCodes["FalseOperandValueError"])
            var = sym1/sym2
            return var
        
        def Execute(self):
            if self._opcode.lower() == 'add' or 'sub' or 'mul' or 'idiv':
                TypeController.checkTypesThreeArgs(self._argList[0].GetArgType(), self._argList[1].GetArgType(), 
                                               self._argList[2].GetArgType(), "int", "int", "int")
                #calling appropriate function
                getattr(self, self._opcode.capitalize())                     


class FrameInstruction(Instruction):
        def __init__(self, order:int, opcode:str, frames):
            super().__init__(order, opcode)
            self._frames = frames
            self._varName = ""

        def Defvar(self, var):
            if re.match(r'^(GF|LF|TF)@[-$&%*!?_A-Za-z]+[-$&%*!?_A-Za-z0-9]*$', var):
                self._frame, self._varName = var.split('@')
        
            


  
class InstructionFactory:
    
    def __init__(self, order, opcode) -> None:
        self._order = order
        self._opcode = opcode.lower()

    def GetInstructionType(self):
        if self._opcode == "add" or "sub" or "mul" or "idiv" :
            return ArithmeticInstruction(self._order, self._opcode)
        if self._opcode == "move" or "createframe" or "popframe" or "defvar":
            return FrameInstruction(self._order, self._opcode)


class TypeController:
    def checkTypesThreeArgs(type1, type2, type3, expectedType1, expectedType2, expectedType3):
        if(type1 != expectedType1 or type2 != expectedType2 or type3 != expectedType3):
            exit(exitCodes["FalseOperandTypeError"])
    
        
class InstructionArguments:

    def __init__(self, type, value) -> None:
        self._argType = type
        self._argValue = value

    def GetArgType(self):
        return self._argType[0]
    
    def GetArgValue(self):
        return self._argValue


class Interpret:
    def __init__(self) -> None:
        pass
        

instructionList = []         
args = ArgsParser()
args.ProcessArgs()
tree = args.GetXmlTree()
root = tree.getroot()
for ins in root:
    instructionProps = list(ins.attrib.values())
    instruction = InstructionFactory(int(instructionProps[0]), instructionProps[1]).GetInstructionType()

    for arg in ins:
        instructionArg = InstructionArguments(list(arg.attrib.values()), arg.text)
        instruction.AddArgument(instructionArg)

    instructionList.append(instruction)
        
instructionList.sort(key=lambda x: x.GetOrder())


instructionList[0].GetOrder()








                

