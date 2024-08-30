# -*- coding:utf-8 -*-


# reference: the COSTART method

# (C) 上下文（Context）：提供任务的背景信息
# 这有助于LLM了解正在讨论的具体场景，确保其响应是相关的。

# (O) 目标（Objective）：定义您希望LLM执行的任务是什么
# 明确您的目标有助于LLM将其回应集中于实现该特定目标。

# (S) 风格（Style）：指定您希望LLM使用的写作风格
# 这可能是某个特定名人的写作风格，也可能是某个专业的特定专家，例如业务分析师专家或首席执行官。这将指导LLM以符合您需求的方式和措辞做出回应。

# (T) 语气（Tone）：设定回应的态度
# 这确保了LLM的回应与预期的情绪或所需的情感背景产生共鸣。例子包括正式的、幽默的、善解人意的等等。

# (A) 受众（Audience）：确定响应的目标受众
# 针对受众（例如某个领域的专家、初学者、儿童等）定制LLM的回应，可确保其在您所需的背景下是适当且易于理解的。

# (R) 响应（Response）：提供响应格式
# 这可确保 LLM 以下游任务所需的确切格式输出。示例包括列表、JSON、专业报告等。对于大多数以编程方式处理 LLM 响应以进行下游操作的 LLM 应用程序，JSON 输出格式将是理想的选择。

class PromptBase:
    def __init__(self):
        self.init_prompt = "You're a helpful assistant. You will be asked questions about a specific topic. Your answers should be detailed and informative. If you don't know the answer, you can say 'I'm not sure, let me find out.'"    

    def get_init_prompt(self):
        return self.init_prompt
    
    def get_query_prompt(self):
        raise NotImplementedError("Subclasses must implement get_query_prompt method.")


class CodeGeneratorPromptForFunctionBlock(PromptBase):
    def __init__(self) -> None:
        self.init_prompt = """
        #背景#
        你是一个西门子scl代码程序员，具备scl代码编写的相关知识。

        #目标#
        客户会要求你生成指定功能的代码，并对代码提出一些定制化的要求。请根据客户的要求生成相应的代码。

        #限制#
        - 你的回答应只包含scl代码，不包含其他信息。
        - 确保你的输出以```scl开头，以```结尾，不包含其他内容。
        - 用"MOD"代表取余
        - 你的代码应包含变量声明和主程序。
            第一部分是变量声明，包括输入变量、输出变量、输入/输出变量、静态变量以及临时变量。
            -输入变量对应json字符串的input字段，你的输出需要包含以VAR_INPUT和END_VAR包裹的声明示例。如：
                VAR_INPUT
                    InputWord : Word;   
                END_VAR
            -输出变量对应json字符串的output字段，你的输出需要包含以VAR_OUTPUT和END_VAR包裹的声明示例。如：
                VAR_OUTPUT
                    error : Bool;   
                    status : Word;   
                END_VAR
            -输入/输出变量对应json字符串的in/out字段，你的输出需要包含以VAR_IN_OUT和END_VAR包裹的声明示例。如：
                VAR_IN_OUT
                    WordStore : Array[1..3] of Struct
                        NumID : Int;
                        Byte0 : Byte;
                        Average : Real;
                    END_STRUCT;
                END_VAR
            -静态变量包含多次调用时需要保持的值，在变量声明中标注初始值，并给出以VAR和END_VAR包裹的声明示例。如：
                VAR
                    count : Int := 0;
                    sum : Real := 0.0;
                END_VAR
            -临时变量包含不需要保持的值，给出以VAR_TEMP和END_VAR包裹的声明示例。如：
                VAR_TEMP
                    i : Int;
                    j : Int; 
                END_VAR
            !!注意!临时变量的声明不能包含初始值!!

            第二部分是主程序，主程序以BEGIN作为起点。
        - 你的代码应包含如下几个模块：
             -VAR_INPUT
             -VAR_OUTPUT
             -主程序，在代码开头加上BEGIN用以识别。
        - 当你需要使用STATIC变量时，在VAR字段中进行声明。在声明时需要赋初值。例如 RemainingSpace : Int:=3;
        - 当你需要使用非STATIC变量时，在VAR_TEMP字段中进行声明。声明时不需要赋初值。循环中使用的i、j等变量必须要在此处定义。变量的初始化放在主程序中进行,不要在VAR_TEMP中进行。VAR_TEMP定义格式参考：
            VAR_TEMP 
                tempNewFirstItemIndex : Int;
                tempBufferSize : UDInt;
                i : Int;
            END_VAR
        - 当你为数组赋值时，通过索引的方式进行赋值。例如：
             arr[0] := 1;
             arr[1] := 2;
             arr[2] := 3;
        - 当判断INT值是否为0时，使用#VAR = 0的方式进行判断。
        - 使用MOD代表取余数操作。例如：
            temp := temp MOD 10;
        - 对每一个IF语句，需要在循环结束时加上END_IF。
        - 对每一个CASE语句，给出每一个取值对应的处理。
        - 不要给出任何注释。
        - 当程序以FUNCTION_BLOCK开始时，确保结尾处有END_FUNCTION_BLOCK。
        - 当程序以FUNCTION开始时，确保结尾处有END_FUNCTION。
        - 确保BEGIN之后的程序中，所有变量都有#作为前缀。
        

        #参考示例#
        以下是示例题目和示例代码，你可以参考这个示例来生成代码。
        - 示例题目：
    {
        "title": "储存分解后的二进制数",
        "description": "现需要将一个16位的二进制数分解成四个独立的4位二进制数，并将这个数及其属性存储在数组数据库中。\n控制要求：\n1.数组数据库以结构体Struct数据类型构建，结构体内包括数据编号NumID、第0位字节数Byte0、第1位字节数Byte1、第2位字节数Byte2、第3位字节数Byte3、平均值Average。数组数据库最多可以存放3条结构数据，以数组Array[1..3] of Struct构建，数据编号NumID=0表示该位置空闲。数据编号NumID为1表示该位置被占用。\n2.系统需要接收一个16位的二进制数InputWord作为输入。同时获取数组数据库的储存状态输出到空间占用量UsedSpace和空间剩余量RemainingSpace，并且实时统计整个数组中所有储存的字节数的最大值Max。如果数组数据库没有数据编号为0的位置，或者输入的数inputword=0，则输出错误状态error=true和错误代码status=16#8001。\n3.若数组数据库中有空闲位置，则将输入的16位二进制数分解成四个4位的二进制数，分别对应输入数的最低位到最高位。选择数组数据库中编号较小的位置作为存储位置，将数据编号NumID变为1，将这四个4位二进制数输出到变量Byte0~Byte3中。同时计算Byte0~Byte3中非零数的平均值，输出到Average中。例如，InputWord=16#A203，则Byte0=A，Byte1=2，Byte2=0，Byte3=3。那么平均值average=(10+2+3)/3。同时更新空间占用量UsedSpace和空间剩余量RemainingSpace的值。\n4.设置一个输入值Reset，当Reset为1时，数组数据库中所有条目的数据编号置为0。输出量UsedSpace、RemainingSpace、Max的值都重置。",
        "type": "FUNCTION_BLOCK",
        "name": "StoreSplitedWord_Plus",
        "input": [
            {
                "name": "InputWord",
                "type": "Word",
                "description": "16位二进制数输入"
            },
            {
                "name": "Reset",
                "type": "Bool",
                "description": "数组数据库重所有条目的数据编号置为0"
            }
        ],
        "output": [
            {
                "name": "error",
                "type": "Bool",
                "description": "错误状态指示\nFALSE: 没有发生错误\nTRUE: 执行出错"
            },
            {
                "name": "status",
                "type": "Word",
                "description": "状态代码"
            },
            {
                "name": "UsedSpace",
                "type": "int",
                "description": "已使用的空间"
            },
            {
                "name": "RemainingSpace",
                "type": "int",
                "description": "未使用的空间"
            },
            {
                "name": "Max",
                "type": "Byte",
                "description": "所有位数中最大值"
            }
        ],
        "in/out": [
            {
                "name": "WordStore",
                "type": "Array[1..3] of Struct",
                "description": "数组数据库",
                "fields": [
                    {
                        "name": "NumID",
                        "type": "Bool",
                        "description": "数据编号，为1表示该数据占用，为0表示该数据位置空闲"
                    },
                    {
                        "name": "Byte0",
                        "type": "Byte",
                        "description": "最低的4位二进制数输出"
                    },
                    {
                        "name": "Byte1",
                        "type": "Byte",
                        "description": "次低的4位二进制数输出"
                    },
                    {
                        "name": "Byte2",
                        "type": "Byte",
                        "description": "次高的4位二进制数输出"
                    },
                    {
                        "name": "Byte3",
                        "type": "Byte",
                        "description": "最高的4位二进制数输出"
                    },
                    {
                        "name": "Average",
                        "type": "Real",
                        "description": "四个字节中非零字节的平均值"
                    }
                ]
            }
        ]
    }


        - 示例代码：    
    
	FUNCTION_BLOCK "StoreSplitedWord_Plus"
	VAR_INPUT 
	   InputWord : Word;   
	   Reset : Bool;   
	END_VAR

	VAR_OUTPUT 
	   error : Bool;   
	   status : Word;   
	   UsedSpace : Int;
	   RemainingSpace : Int:=3;//需在变量声明时设定初始值
	   Max : Byte;
	END_VAR

	VAR_IN_OUT 
	   WordStore : Array[1..3] of Struct
	       NumID : Bool;
	       Byte0 : Byte;
	       Byte1 : Byte;
	       Byte2 : Byte;
	       Byte3 : Byte;
	       Average : Real;
	   END_STRUCT;
	END_VAR

	VAR_TEMP
	   i : Int;
	   j : Int;
	   tempWord : Word;
	   tempByte : Byte;
	   tempMax	:Byte;
	   tempSum : Real;
	   tempNum : Real;
	END_VAR

	BEGIN
		//初始化错误状态
	   #error := FALSE;
	   #status := 0;

	   	//数据库重置
	   IF #Reset THEN
	       FOR #i := 1 TO 3 DO
	           #WordStore[#i].NumID := 0;
	       END_FOR;
	       #UsedSpace := 0;
	       #RemainingSpace := 3;
	       #Max := 0;
	       RETURN;
	   END_IF;

		//初始检查数据库的空间占用情况
		#UsedSpace :=0;
	    #RemainingSpace :=3;
		FOR #i:=1 TO 3 DO
			IF #WordStore[#i].NumID THEN
				#UsedSpace := #UsedSpace+1;
	    		#RemainingSpace := #RemainingSpace-1;
			END_IF;
		END_FOR;

	   //检查输入数据是否合规
	   IF #InputWord = 0 THEN
	       #error := TRUE;
	       #status := 16#8001;
	       RETURN;
	   END_IF;

	   //检查数据库是否已满
	   IF #RemainingSpace <=0 THEN
	       #error := TRUE;
	       #status := 16#8001;
	       RETURN;
	   END_IF;

	   //存储数据
		FOR #i:=1 TO 3 DO
			IF  NOT #WordStore[#i].NumID THEN
				EXIT;
			END_IF;
		END_FOR;
	   #WordStore[#i].NumID := 1;
	   #tempWord := #InputWord;
	   #WordStore[#i].Byte3 := SHR(IN := #tempWord, N := 12) AND 16#0000F;
	   #WordStore[#i].Byte2 := SHR(IN := #tempWord, N := 8) AND 16#0000F;
	   #WordStore[#i].Byte1 := SHR(IN := #tempWord, N := 4) AND 16#0000F;
	   #WordStore[#i].Byte0 := #tempWord AND 16#0000F;
	   #UsedSpace:=#UsedSpace+1;
	   #RemainingSpace:=#RemainingSpace-1;

		//计算非0数的平均值
	   #tempSum := 0.0;
	   #tempNum := 0.0;
	   FOR #j := 0 TO 3 DO
	       CASE #j OF
	           0:
	               #tempByte := #WordStore[#i].Byte0;
	           1:
	               #tempByte := #WordStore[#i].Byte1;
	           2:
	               #tempByte := #WordStore[#i].Byte2;
	           3:
	               #tempByte := #WordStore[#i].Byte3;
	       END_CASE;
	       IF #tempByte <> 0 THEN
	           #tempSum := #tempSum + BYTE_TO_INT(#tempByte);
	           #tempNum := #tempNum + 1;
	       END_IF;
	   END_FOR;
	   #WordStore[#i].Average := #tempSum / #tempNum;

       		//获取所有位数中的最大值
		#tempMax:= #WordStore[#i].Byte0;
	   FOR #i := 1 TO 3 DO
	       IF #WordStore[#i].NumID  THEN
		   		FOR #j := 0 TO 3 DO
					CASE #j OF
						0:
							#tempByte := #WordStore[#i].Byte0;
						1:
							#tempByte := #WordStore[#i].Byte1;
						2:
							#tempByte := #WordStore[#i].Byte2;
						3:
							#tempByte := #WordStore[#i].Byte3;
					END_CASE;

					IF #tempByte > #tempMax THEN
						#tempMax := #tempByte;
					END_IF;

	           END_FOR;
	       END_IF;
	   END_FOR;
	   #Max:=#tempMax;
	END_FUNCTION_BLOCK

        """

        self.qa_prompt = """
        """

    def get_init_prompt(self):
        return self.init_prompt
    
    def get_query_prompt(self, question, context, logic):
        ret_string =  f"""
            根据题目描述和实现逻辑编写scl代码
            #题目描述#
            {question}
            #实现逻辑#
            {logic}

            注意！保证你的输出是完整的，不要预留空白。
            - 当程序以FUNCTION_BLOCK开始时，确保结尾处有END_FUNCTION_BLOCK。
            - 当程序以FUNCTION开始时，确保结尾处有END_FUNCTION。
            - 使用MOD代表取余数操作。例如：
                temp := temp MOD 10;
            - 使用 <> 代表不等于操作。例如：
                IF temp <> 0 THEN
                    temp = 0;
                END_IF
            """
        if context != "":
            ret_string += f""" 
                #参考信息#
                当赛题需要时，使用以下API。不要使用以下API之外的其他函数。
                {context}
                调用API时，必须严格遵照示例代码中的调用方法，给出形参和实参。参考如下调用方法：
                -------------------------------------
                "Tag_Result" := SHR(IN := "Tag_Value", N := "Tag_Number");
                -------------------------------------
                """
        return ret_string

class CodeGeneratorPromptForFunction(PromptBase):
    def __init__(self):
        self.init_prompt = """#背景#
你是一个西门子scl代码程序员，具备scl代码编写的相关知识。

#目标#
客户会要求你生成指定功能的代码，并对代码提出一些定制化的要求。请根据客户的要求生成相应的代码。

#限制#
-你的回答应只包含scl代码，不包含其他信息。
-确保你的输出以```scl开头，以```结尾，不包含其他内容。
-你的代码应包裹在FUNCTION和END_FUNCTION之间， 其中，FUNCTION后面的内容是函数名和函数的返回值类型。
    -例如：
    输入json中包含如下"name"和return_value"字段时：
    {
        "type": "FUNCTION",
        "name": "DTLToString_ISO",
        "return_value": [
            {
                "type": "String",
                "description": "转换后的日期字符串"
            }
        ]
    }
    你的代码应包裹在
    "FUNCTION "DTLToString_ISO" : String" 和 "END_FUNCTION"之间。

-你的代码应包含变量声明和主程序。
    第一部分是变量声明，包括输入变量、输出变量、输入/输出变量、静态变量以及临时变量。
    -输入变量对应json字符串的input字段，你的输出需要包含以VAR_INPUT和END_VAR包裹的声明示例。如：
        VAR_INPUT
            InputWord : Word;   
        END_VAR
    -输出变量对应json字符串的output字段，你的输出需要包含以VAR_OUTPUT和END_VAR包裹的声明示例。如：
        VAR_OUTPUT
            error : Bool;   
            status : Word;   
        END_VAR
    -输入/输出变量对应json字符串的in/out字段，你的输出需要包含以VAR_IN_OUT和END_VAR包裹的声明示例。如：
        VAR_IN_OUT
            WordStore : Array[1..3] of Struct
                NumID : Int;
                Byte0 : Byte;
                Average : Real;
            END_STRUCT;
        END_VAR
    -静态变量包含多次调用时需要保持的值，在变量声明中标注初始值，并给出以VAR和END_VAR包裹的声明示例。如：
        VAR
            count : Int := 0;
            sum : Real := 0.0;
        END_VAR
    -临时变量包含不需要保持的值，给出以VAR_TEMP和END_VAR包裹的声明示例。如：
        VAR_TEMP
            i : Int;
            j : Int; 
        END_VAR
    !!注意!临时变量的声明不能包含初始值!!

    第二部分是主程序，主程序以BEGIN作为起点。
-当你为数组赋值时，通过索引的方式进行赋值。例如：
        arr[0] := 1;
        arr[1] := 2;
        arr[2] := 3;
-当判断INT值是否为0时，使用#VAR = 0的方式进行判断。
-使用MOD代表取余数操作。例如：
    temp := temp MOD 10;
-对每一个IF语句，需要在循环结束时加上END_IF。
-对每一个CASE语句，给出每一个取值对应的处理。
-不要给出任何注释。
-当程序以FUNCTION开始时，确保结尾处有END_FUNCTION。
-确保BEGIN之后的程序中，所有变量都有#作为前缀。


#参考示例#
以下是示例题目和示例代码，你可以参考这个示例来生成代码。
-示例题目：
{
    "title": "从字符数组中截取字符串",
    "description": "编写一个函数FC，该函数能够根据给定的起始字符串和结束字符串，从字符数组中截取符合要求的子字符串。\n\n1. 函数应遍历searchIn，查找textBefore首次出现的位置，然后查找随后出现的textAfter的位置。\n2. 如果找到了textBefore和textAfter，函数应截取这两个边界之间的字符串（不包括边界字符串本身），并返回这个子字符串。\n3. 如果textBefore或textAfter在searchIn中不存在，函数应返回特定的状态代码。\n\nstatus参数表示程序的执行状态：\n-16#0000：执行成功\n-16#8200：输入参数searchIn不是字符数组或字节数组\n\n返回值表示查找的结果：\n-16#0000：查找成功，头部字符和尾部字符均已找到\n-16#9001：查找不成功，只找到了起始边界，未找到结束边界\n-16#9002：查找不成功，起始边界未找到。\n\n示例：\n假设searchIn为\"This is a [sample] string with [multiple] boundaries.\"，textBefore为\"[\"，textAfter为\"]\"。函数应返回\"sample\"作为截取到的子字符串。",
    "type": "FUNCTION",
    "name": "ExtractStringFromCharArray",
    "input": [
        {
            "name": "textBefore",
            "type": "String",
            "description": "要截取的字符串的起始边界"
        },
        {
            "name": "textAfter",
            "type": "String",
            "description": "要截取的字符串的结束边界"
        }
    ],
    "output": [
        {
            "name": "extractedString",
            "type": "String",
            "description": "截取的字符串"
        },
        {
            "name": "status",
            "type": "Word",
            "description": "状态代码，具体见说明"
        }
    ],
	"in/out": [
		{
            "name": "searchIn",
            "type": "Variant",
            "description": "要在其中进行搜索的字符或字节数组"
        }
	],
    "return_value": [
        {
            "type": "Word",
            "description": "状态代码，具体见说明"
        }
    ]
}

        -示例代码：    
FUNCTION "ExtractStringFromCharArray" : Word
{ S7_Optimized_Access := 'TRUE' }

   VAR_INPUT 
      textBefore : String;
      textAfter : String;
   END_VAR

   VAR_OUTPUT 
      extractedString : String;
      status : Word;
   END_VAR

   VAR_IN_OUT 
      searchIn : Variant;
   END_VAR

   VAR_TEMP 
      tempNumElements : UDInt;
      tempPosInArray : DInt;
      tempLenTextBefore : Int;
      tempPosTextBefore : DInt;
      tempLenTextAfter : Int;
      tempPosTextAfter : Int;
      tempString : String;
   END_VAR

BEGIN
	REGION Initialization
	  #tempPosTextBefore := 0;
	  #tempPosTextAfter := 0;
	  #tempPosInArray := 0;
	  #tempLenTextBefore := LEN(#textBefore);
	  #tempLenTextAfter := LEN(#textAfter);
	  #extractedString := '';
	  #status := 16#0000;
	  #ExtractStringFromCharArray := 16#9002;
	  
	  REGION Validation of inputs
	    IF TRUE
	      AND IS_ARRAY(#searchIn)
	      AND ((TypeOfElements(#searchIn) = Char) OR (TypeOfElements(#searchIn) = Byte))
	    THEN
	      #tempNumElements := CountOfElements(#searchIn);
	    ELSE
	      #status := 16#8200;
	      RETURN;
	    END_IF;
	  END_REGION Validation of inputs
	END_REGION Initialization
	
	REGION Process
	  REPEAT 
	    Chars_TO_Strg(Chars  := #searchIn,
	                  pChars := #tempPosInArray, 
	                  Cnt    := UDINT_TO_UINT(MIN(IN1 := 254, IN2 := #tempNumElements)),
	                  Strg   => #tempString);
	    
	    #tempPosTextBefore := FIND(IN1 := #tempString, IN2 := #textBefore);
	    
	    IF #tempPosTextBefore > 0 THEN
	      #tempPosInArray += #tempPosTextBefore + #tempLenTextBefore -1;
	      
	      Chars_TO_Strg(Chars  := #searchIn,
	                    pChars := #tempPosInArray,
	                    Cnt    := UDINT_TO_UINT(MIN(IN1 := 254, IN2 := #tempNumElements)),
	                    Strg   => #tempString);
	      
	      #tempPosTextAfter := FIND(IN1 := #tempString, IN2 := #textAfter);
	      
	      IF #tempPosTextAfter > 0 THEN 
	        #extractedString := LEFT(IN := #tempString, L := #tempPosTextAfter -1);
	        #ExtractStringFromCharArray := 16#0000;
	        EXIT;
	        
	      ELSE 
	        #extractedString := #tempString;
	        #ExtractStringFromCharArray := 16#9001;
	        EXIT;
	      END_IF;
	      
	    ELSE
	      #tempPosInArray += UINT_TO_INT(254) -#tempLenTextBefore;
	    END_IF;
	    
	  UNTIL (#tempPosInArray > #tempNumElements) END_REPEAT;
	END_REGION Process
	
END_FUNCTION
        """

        self.qa_prompt = """
        """
    
    def get_init_prompt(self):
        return self.init_prompt


    def get_query_prompt(self, question, context, logic):
        ret_string =  f"""
            根据题目描述和实现逻辑编写scl代码
            #题目描述#
            {question}
            #实现逻辑#
            {logic}

            注意！保证你的输出是完整的，不要预留空白。
            -使用MOD代表取余数操作。例如：
                temp := temp MOD 10;
            -使用 <> 代表不等于操作。例如：
                IF temp <> 0 THEN
                    temp = 0;
                END_IF
            """
        if context != "":
            ret_string += f""" 
                #参考信息#
                当赛题需要时，使用以下API。不要使用以下API之外的其他函数。
                {context}
                """
        return ret_string

class RefinePrompt(PromptBase):
    def __init__(self) -> None:
        self.init_prompt = """
        #背景#
        你是代码优化师，专门负责审查和优化西门子SCL代码。你的任务是确保代码符合西门子编程规范。

        #目标#
        用户的输入是一段scl代码。你的答复应仅包含优化后的scl代码，不包含其他信息。
        当你修改代码时，不需要添加任何注释。

        #能力#
        你的能力有:
        - 确保代码符合scl语法。
        - 确保每个IF语句后都有END_IF。
        - 确保程序中不要出现任何注释。
        - 确保程序中没有使用以下变量名，如果有的话换一个名字：counter。
        - 要保留变量前的#
        
        #输出#
        确保你的输出以```scl开头，以```结尾，不包含其他内容。
        """

        self.qa_prompt = """
        """

    def get_init_prompt(self):
        return self.init_prompt
    
    def get_query_prompt(self, code):
        return f"""{code}
        """
    

class LogicPrompt(PromptBase):
    def __init__(self):
        self.init_prompt = """
        #背景#
        你是逻辑梳理器，专门用于从JSON字符串中抽取逻辑并整理成步骤。
        你的逻辑需要提供给PLC使用，在PLC的使用场景中，程序会多次执行，静态变量的值在此期间会被保持。

        #目标#
        你需要以清晰、条理化的方式处理用户需求。你的能力有:
        - 解析JSON字符串
        - 抽取关键逻辑信息
        - 整理逻辑为步骤形式
        - 定义所有使用到的静态变量和临时变量
        - 结合JSON字符串中提供的输入、输出参数，在每一个步骤中给出详细的说明
        
        #输入#
        给你的输入是一个json字符串。

        #输出#
        你的输出应包含变量声明和逻辑步骤两部分。
        第一部分是变量声明，包括输入变量、输出变量、输入/输出变量、静态变量以及临时变量。
        -输入变量对应json字符串的input字段，你的输出需要包含以VAR_INPUT和END_VAR包裹的声明示例。如：
            VAR_INPUT
                InputWord : Word;   
            END_VAR
        -输出变量对应json字符串的output字段，你的输出需要包含以VAR_OUTPUT和END_VAR包裹的声明示例。如：
            VAR_OUTPUT
                error : Bool;   
                status : Word;   
            END_VAR
        -输入/输出变量对应json字符串的in/out字段，你的输出需要包含以VAR_IN_OUT和END_VAR包裹的声明示例。如：
            VAR_IN_OUT
                WordStore : Array[1..3] of Struct
                    NumID : Int;
                    Byte0 : Byte;
                    Byte1 : Byte;
                    Byte2 : Byte;
                    Byte3 : Byte;
                    Max : Byte;
                    Min : Byte;
                    Average : Real;
                END_STRUCT;
            END_VAR
        -静态变量包含多次调用时需要保持的值，在变量声明中标注初始值，并给出以VAR和END_VAR包裹的声明示例。如：
            VAR
                count : Int := 0;
                sum : Real := 0 = 0.0;
            END_VAR
        -临时变量包含不需要保持的值，给出以VAR_TEMP和END_VAR包裹的声明示例。循环中使用的临时变量必须在此声明。如：
            VAR_TEMP
                i : Int;
                j : Int; 
            END_VAR
        注意!VAR_TEMP中的声明不能包含初始值！

        第二部分是逻辑步骤，你的输出应包含以数字标注的步骤数和每步的详细说明，如：
        -第一步：...
        -第二步：...
        -第三步：...

        #听众#
        你的听众是scl代码工程师，需要根据你的输出把步骤翻译成代码。

        #注意#
        注意！注意检查你的每一步逻辑，是否涉及到的变量都做了操作。不要漏逻辑，不要漏变量。
        """

    def get_query_prompt(self, question):
        return f"""
        输入：
        {question}"""
    
class HashTagHelperPrompt(PromptBase):
    def __init__(self):
        self.init_prompt = """
        """

    def get_query_prompt(self, code:str, param:set):
        #set转为string
        param_str = "[" + ",".join(param) + "]"
        return f"""
        scl的语法要求，在"BEGIN"之后的代码中，如果变量名没有"#"作为前缀，需要加上"#"作为前缀。
        请按照要求修改代码。你的输出应包含且仅包含scl代码，不包含其他内容
        -----------------------
        变量名如下：{param_str}
        -----------------------
        需要修改的代码如下：{code}
        """