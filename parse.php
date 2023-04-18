<?php
ini_set('display_errors','stderr');
define("IPP_HEAD", ".IPPcode23");

$types = array(
    1 => 'int',
    2 => 'bool',
    3 => 'string',
    4 => 'nil',
    5 => 'label',
    6 => 'type',
    7 => 'var'
);

$whiteSpace = array(
    "tab" => '\t',
    "newline" => '\n',
    "verTab" => '\x0B',
    "space" => '' 
);

$withoutArg = array(
    'CREATEFRAME' => true,
    'PUSHFRAME' => true,
    'POPFRAME' => true,
    'RETURN' => true,
    'BREAK' => true
);

$oneLabel = array(
    'CALL' => true,
    'LABEL' => true,
    'JUMP' => true
);

$oneVar = array(
    'DEFVAR' => true,
    'POPS' => true
);

$oneSymb = array(
    'EXIT' => true,
    'DPRINT' => true,
    'WRITE' => true,
    'PUSHS' => true
);

$varAndSymb = array(
    'MOVE' => true,
    'INT2CHAR' => true,
    'STRLEN' => true,
    'TYPE' => true
);

$varSymb1Symb2 = array(
    'ADD' => true,
    'SUB' => true,
    'MUL' => true,
    'IDIV' => true,
    'LT' => true,
    'GT' => true,
    'EQ' => true,
    'AND' => true,
    'OR' => true,
    'NOT' => true,
    'STRI2INT' => true,
    'CONCAT' => true,
    'GETCHAR' => true,
    'SETCHAR' => true
);

$labelSymb1Symb2 = array(
    'JUMPIFEQ' => true,
    'JUMPIFNEQ' => true,
);

$typeInstruction = 'READ';

$headerOk = false;
$xw = new XMLWriter();
$instructCount = 0;
startXMLwriter();

checkParams();

while ($line = fgets(STDIN))
{
    $line = ModifyLine($line);
    $line = splitLine($line);
    $instruction = strtoupper($line[0]);
    if($instruction == $whiteSpace["newline"] || $instruction == $whiteSpace["verTab"] || $instruction == $whiteSpace["tab"] || $instruction == $whiteSpace["space"])
    {
        continue;
    }
    if(!$headerOk)
    {
        checkHeader($line[0]);
        $headerOk = true;
        continue;
    }
    
    if(isset($withoutArg[$instruction]))
    {
        checkArgAmount(0,$line);
        printInstruction($line,$instructCount);
        continue;
    }

    elseif(isset($oneVar[$instruction]))
    {
        checkArgAmount(1,$line);
        $type = checkVar($line[1]);
        if($type != 0)
        {
            printInstruction($line,$instructCount,$types[$type]);
            continue;
        }
        exit(23);
    }

    elseif(isset($oneLabel[$instruction]))
    {
        checkArgAmount(1,$line);
        $type = checkLabel($line[1]);
        if($type != 0)
        {
            printInstruction($line,$instructCount, $types[$type]);
            continue;
        }
        exit(23);            
    }

    elseif(isset($oneSymb[$instruction]))
    {
        checkArgAmount(1,$line);
        $type = checkSymbol($line[1]);
        if($type != 0)
        {
            printInstruction($line,$instructCount, $types[$type]);
            continue;
        }
        exit(23);
    }

    elseif(isset($varAndSymb[$instruction]))
    {
        checkArgAmount(2,$line);
        $type = checkVar($line[1]);
        $type2 = checkSymbol($line[2]);
        if($type != 0 && $type2 != 0)
        {
            printInstruction($line,$instructCount, $types[$type], $types[$type2]);
            continue;
        }
        exit(23);
    }

    elseif(isset($varSymb1Symb2[$instruction]))
    {
        checkArgAmount(3,$line);
        $type = checkVar($line[1]);
        $type2 = checkSymbol($line[2]);
        $type3 = checkSymbol($line[3]);
        if($type != 0  && $type2 != 0 && $type3 != 0)
        {
            printInstruction($line,$instructCount, $types[$type], $types[$type2], $types[$type3]);
            continue;
        }
        exit(23);        
    }

    elseif(isset($labelSymb1Symb2[$instruction]))
    {
        checkArgAmount(3,$line);
        $type = checkLabel($line[1]);
        $type2 = checkSymbol($line[2]);
        $type3 = checkSymbol($line[3]);
        if($type != 0 && $type2 != 0 && $type3 != 0)
        {
            printInstruction($line,$instructCount, $types[$type], $types[$type2], $types[$type3]);
            continue;
        }        
        exit(23);
    }

    elseif($typeInstruction == $instruction)
    {
        checkArgAmount(2,$line);
        $type = checkVar($line[1]);
        $type2 = checkType($line[2]);
        if($type == 7 && $type2 == 6)
        {
            printInstruction($line, $instructCount, $types[$type], $types[$type2]);
            continue;
        }
        exit(23);
    }

    else
    {
        exit(22);
    }
}

endXMLwriter();
exit(0);

function checkVar(&$arg)
{
    if(preg_match("/^(GF|LF|TF)@[\-\$&%\*!\?_A-Za-z]+[\-\$&%\*!\?_A-Za-z0-9]*$/", $arg, $matches))
    {
        $arg = $matches[0];
        return 7;
    }
    return 0;
}

function checkLabel(&$arg)
{
    if(preg_match("/^[\-\$&%\*!\?_A-Za-z]+[\-\$&%\*!\?_A-Za-z0-9]*$/", $arg, $matches))
    {
        $arg = $matches[0];
        return 5;
    }
    return 0;
}

function checkType(&$arg)
{
    if(preg_match("/^int|string|bool$/",$arg, $matches))
    {
        $arg = $matches[0];
        return 6;
    }
    return 0;
}

function checkConst(&$arg)
{
    if(preg_match("/^int@[-+]*[0-9]+$/", $arg, $matches))
    {
        $splitstring = explode('@', $matches[0]);
        $arg = $splitstring[1];
        return 1;
    }
    elseif(preg_match("/^bool@((true|false){1})$/",$arg, $matches))
    {
        $splitstring = explode('@', $matches[0]);
        $arg = strtolower($splitstring[1]);
        return 2;
    }


    elseif(preg_match("/^string@((\\\\[0-9]{3})*([^\\\\\s#]*))*([^\\\\\s#]|\\\\[0-9]{3})$|^string@$/",$arg, $matches))
    {
        $splitstring = explode('@', $matches[0]);
        $arg = $splitstring[1];
        return 3;
    }

    elseif(preg_match("/^nil@nil$|^nil@$/", $arg, $matches))
    {
        $splitstring = explode('@', $matches[0]);
        $arg = $splitstring[1];
        return 4;
    }

    return 0;
}

function checkSymbol(string &$arg)
{
    $returnConst = checkConst($arg);
    if($returnConst != 0)
    {
        return $returnConst;
    }
    else
        return checkVar($arg);
}

function printInstruction($line, string &$instructCount, $type1 = "var", $type2 = "var", $type3 = "var")
{
    $instructCount++;
    switch(count($line))
    {
        case 1:
            printNoArgsInstruct($line, $instructCount);
            break;
        case 2:
            printOneArgInstruct($line, $instructCount, $type1);
            break;
        case 3:
            printTwoArgInstruct($line, $instructCount, $type1, $type2);
            break;
        case 4:
            printThreeArgInstruct($line, $instructCount, $type1, $type2, $type3); 
            break;
    }
}
function checkVarArgInstruct(string $variable)
{
    if(!preg_match("/^(GF|LF|TF)@[\-\$&%\*!\?_A-Za-z]+[\-\$&%\*!\?_A-Za-z0-9]*$/", $variable))
    {
        return false;
    }
    return true;
}

function printOneArgInstruct($line, string $instructCount, string $type1)
{
    global $xw;
    $xw->startElement("instruction");
    $xw->writeAttribute('order', $instructCount);
    $xw->writeAttribute('opcode', strtoupper($line[0]));

    $xw->startElement("arg1");
    $xw->writeAttribute('type', $type1);
    $xw->text($line[1]);
    $xw->endElement();
    $xw->endElement();

    
}
function printThreeArgInstruct($line, string $instructCount, string $type1, string $type2, string $type3)
{
    global $xw;
    $xw->startElement("instruction");
    $xw->writeAttribute('order', $instructCount);
    $xw->writeAttribute('opcode', strtoupper($line[0]));

    $xw->startElement("arg1");
    $xw->writeAttribute('type', $type1);
    $xw->text($line[1]);
    $xw->endElement();

    $xw->startElement("arg2");
    $xw->writeAttribute('type', $type2);
    $xw->text($line[2]);
    $xw->endElement();

    $xw->startElement("arg3");
    $xw->writeAttribute('type', $type3);
    $xw->text($line[3]);
    $xw->endElement();
    $xw->endElement();

}
function printTwoArgInstruct($line, string $instructCount, string $type1, string $type2)
{
    global $xw;
    $xw->startElement("instruction");
    $xw->writeAttribute('order', $instructCount);
    $xw->writeAttribute('opcode', strtoupper($line[0]));

    $xw->startElement("arg1");
    $xw->writeAttribute('type', $type1);
    $xw->text($line[1]);
    $xw->endElement();

    $xw->startElement("arg2");
    $xw->writeAttribute('type', $type2);
    $xw->text($line[2]);
    $xw->endElement();
    $xw->endElement();
}

function printNoArgsInstruct($line, string $instructCount)
{
    global $xw;
    $xw->startElement("instruction");
    $xw->writeAttribute('order', $instructCount);
    $xw->writeAttribute('opcode', strtoupper($line[0]));
    $xw->endElement();
}
function splitLine(string $line)
{
    return explode(' ',$line);
}
function ModifyLine(string $line)
{
    $line = DeleteComments($line);
    $line = DelEdgeWhiteSpace($line);
    return $line;
}
function DelEdgeWhiteSpace(string $line)
{
    return trim($line);
}
function DeleteComments(string $line)
{
    $split = explode('#', $line);
    return $split[0];
}

function checkHeader(string $head)
{
    if(!($head == IPP_HEAD))
    {
        exit(21);
    }
}

function startXMLwriter()
{
    global $xw;
    $xw->openMemory();
    $xw->setIndent(true);
    $xw->setIndentString(' ');
    $xw->startDocument("1.0", "UTF-8");
    $xw->startElement("program");
    $xw->writeAttribute("language","IPPcode23");
}

function endXMLwriter()
{
    global $xw;
    $xw->endElement();
    $xw->endDocument();
    echo $xw->outputMemory();
    exit(0);
}

function checkParams()
{
    global $argv;
    if(isset($argv[1]))
    {
        if($argv[1] == "--help")
        {
            if(isset($argv[2]))
            {
                exit(10);
            }
            echo("skript parse.php načte ze standardního vstupu zdrojový kód v IPPcode23, zkontroluje 
            lexikální a syntaktickou správnost programu a vypíše na standardní
            výstup XML reprezentaci programu dle specifikace v sekci 3.1.
            Tento skript pracuje s těmito parametry: --help
            Chybové návratové kódy specifické pro parser:
            - 21 - chybná nebo chybějící hlavička ve zdrojovém kódu zapsaném v IPPcode23;
            - 22 - neznámý nebo chybný operační kód ve zdrojovém kódu zapsaném v IPPcode23;
            - 23 - jiná lexikální nebo syntaktická chyba zdrojového kódu zapsaného v IPPcode23.\n");
            exit(0);
        }
        else
        {
            exit(10);
        }
    }
}

function checkArgAmount($amount, $line)
{
    if(count($line) != $amount+1)
    {
        exit(23);
    }
}