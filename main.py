
import instructor
from google import genai
from pydantic import BaseModel , Field
import json, sys

SYSTEM_PROMOT= """
You are a Professional Industrial Equipment Monitoring and Maintenance Assistant. Your role is to assess equipment conditions by retrieving sensor data and maintenance history, identifying potential risks, consulting the safety protocol tool, and finding suitable maintenance personnel when necessary. Base your assessments and recommendations on tool results, prioritize industrial safety, and never invent data or claim that an action has been performed unless confirmed. You are an advisory assistant, not an autonomous safety controller; all safety-critical interventions must follow approved site procedures and be authorized by qualified personnel.
Finally, Give conclusion from data collected.
<example>### Equipment Assessment Report: C-101 (Compressor)

#### 1. Sensor Data Readings
* **Vibration:** 12.5 mm/s
* **Temperature:** 95 °C
* **Pressure:** 45 bar

#### 2. Maintenance History
* **Last Maintenance:** 2024-01-15 (10 days ago)
* **Maintenance Type:** Routine inspection
* **Recent Issues:** Minor bearing wear noted during the last inspection.

#### 3. Safety Protocol & Risk Evaluation
* **Risk Level:** High
* **Recommended Action:** **IMMEDIATE_SHUTDOWN** (Critical operating conditions detected; response time: ASAP).

#### 4. Available Emergency Personnel
* **Required Skill:** Compressor Technician
* **Urgency:** Critical
* **Available Personnel:**
  * **Ahmed Hassan** (Experience: 12 years, Location: On-site)
  * **Mohammed Ali** (Experience: 8 years, Location: On-call)
* **Estimated Response Time:** 15 minutes

---

### Conclusion
Equipment C-101 is currently operating under critical conditions with elevated vibration (12.5 mm/s) and temperature (95 °C), following previous observations of minor bearing wear. Based on the safety protocols, an **immediate shutdown** is required. 

*Please note: As an advisory assistant, I cannot perform autonomous safety interventions. All safety-critical interventions (such as initiating the shutdown and dispatching personnel) must follow approved site procedures and be authorized by qualified personnel.* We recommend immediately notifying on-site technician **Ahmed Hassan** to initiate emergency shutdown and inspection procedures.</example>
"""

client=instructor.from_provider("google/gemini-3.5-flash-lite")
ai = genai.Client()


#Tool01
class GetSensorData(BaseModel):
    """Get real-time sensor readings for equipment."""
    equipment_id: str = Field(description="Equipment ID",examples=["C-101","P-205"])



#Tool01 Function
def get_sensor_data(equipment_id: str) -> dict:
    sensors = {
        "C-101": {
            "vibration_mm_s": 12.5,  # HIGH
            "temperature_c": 95,      # HIGH
            "pressure_bar": 45,       # NORMAL
        },
        "P-205": {
            "vibration_mm_s": 2.1,
            "temperature_c": 45,
            "pressure_bar": 30,
        }
    }
    return sensors.get(equipment_id, {"error": "Equipment not found"})

#----------
#Tool02
class GetMaintenanceHistory(BaseModel):
    """Get recent maintenance records for equipment."""
    equipment_id: str = Field(description="Equipment ID")
    days_back: int = Field(description="How many days of history to check", default=30)

#Tool02 Function
def get_maintenance_history(equipment_id: str, days_back: int) -> dict:
    history = {
        "C-101": {
            "last_maintenance": "2024-01-15",  # 10 days ago
            "days_since_maintenance": 10,
            "maintenance_type": "Routine inspection",
            "issues_found": ["Minor bearing wear noted"],
            "next_scheduled": "2024-02-15"
        },
        "P-205": {
                    "last_maintenance": "2024-01-15",  # 10 days ago
                    "days_since_maintenance": 10,
                    "maintenance_type": "Routine inspection",
                    "issues_found": [],
                    "next_scheduled": "2024-02-15"
                }
    }
    return history.get(equipment_id, {"error": "No maintenance records"})


#---------
#Tool03
class GetSafetyProtocol(BaseModel):
    """Get safety protocols based on equipment status."""
    equipment_type: str = Field(description="Type in low case letters",examples=["compressor","pump","valve"])
    vibration_level: float = Field(description="Current vibration in mm/s unit")
    temperature_c: float = Field(description="Current temperature in Celsius unit")

#Tool3 Function
def get_safety_protocol(equipment_type: str, vibration_level: float, temperature_c: float) -> dict:
    # Safety logic
    if vibration_level > 10 or temperature_c > 90:
        return {
            "action": "IMMEDIATE_SHUTDOWN",
            "reason": "Critical operating conditions detected",
            "risk_level": "HIGH",
            "response_time": "ASAP"
        }
    elif vibration_level > 7 or temperature_c > 80:
        return {
            "action": "MONITOR_CLOSELY",
            "reason": "Elevated readings but within tolerance",
            "risk_level": "MEDIUM",
            "response_time": "Within 4 hours"
        }
    else:
        return {
            "action": "CONTINUE_OPERATION",
            "reason": "Normal operating conditions",
            "risk_level": "LOW",
            "response_time": "Next scheduled maintenance"
        }



#------
#Tool04
class GetAvailablePersonnel(BaseModel):
    """Get available maintenance personnel for emergency response. Run this Tool according to the last results of get_safety_protocol function"""
    skill_required: str = Field(description="Required skill: 'compressor_technician', 'electrician', 'mechanic'")
    urgency: str = Field(description="Urgency level: 'critical', 'high', 'normal'")
#Tool04 Function
def get_available_personnel(skill_required: str, urgency: str) -> dict:
    personnel = {
        "compressor_technician": {
            "available": [
                {"name": "Ahmed Hassan", "experience_years": 12, "location": "On-site"},
                {"name": "Mohammed Ali", "experience_years": 8, "location": "On-call"}
            ],
            "response_time_minutes": 15 if urgency == "critical" else 60
        }
    }
    return personnel.get(skill_required, {"error": "No personnel available"})

all_tools=[{
    'type': "function",
    'name': "get_sensor_data",
    'parameters': GetSensorData.model_json_schema()
},{
    'type': "function",
    'name': "get_maintenance_history",
    'parameters': GetMaintenanceHistory.model_json_schema()
},
    {
    'type': "function",
    'name': "get_safety_protocol",
    'parameters': GetSafetyProtocol.model_json_schema()
},
{
    'type': "function",
    'name': "get_available_personnel",
    'parameters': GetAvailablePersonnel.model_json_schema()

}]

#----------
id=""
print("""
The Ai response:
Hello, I am the assisatant responsible on checking the equipements and make the decisions""")
while(True):
    promot=input("\nThe user: ")
    if promot == "\\exit":
        print("""
The Ai response:
Session ended. If you need assistance with industrial equipment monitoring in the future, feel free to return. Goodbye!""")
        break

    # Start the conversation with the user's prompt
    current_input = f"""According to the user prompt decide if you want to run the tools or no!
    <user_prompt>{promot}</user_prompt>
    If there is missing imperative information such as equipment id (ONLY!), tell the user about them without calling the tool."""
    
    # INNER LOOP: Keep calling LLM until it stops requesting tools
    while True:
        optionai = {
            "model": "gemini-3.5-flash-lite",
            "input": current_input,
            "tools": all_tools,
            "system_instruction": SYSTEM_PROMOT
        }
        if id:
            optionai["previous_interaction_id"] = id

        interaction = ai.interactions.create(**optionai)
        id = interaction.id  # Update conversation ID

        tool_calls = [s for s in interaction.steps if s.type == "function_call"]
        
        if not tool_calls:
            # NO TOOLS CALLED -> The LLM is done
            print(f"\nThe Ai response:\n{interaction.output_text}\n")
            break  # Exit the INNER loop, go back to waiting for user input

        # TOOLS CALLED -> Execute themC
        function_results = []
        
        for call in tool_calls:
            if call.name == "get_sensor_data":
                print("Getting Sensors Data...")
                result = get_sensor_data(**call.arguments)
            elif call.name == "get_maintenance_history":
                fc2valid=GetMaintenanceHistory.model_validate(call.arguments)
                print("Getting Maintenance History...")
                result= get_maintenance_history(**fc2valid.model_dump())
            elif call.name == "get_safety_protocol":
                print("Getting Safety Protocol...")
                result = get_safety_protocol(**call.arguments)
            elif call.name == "get_available_personnel":
                print("Getting Available Personnel...")
                result = get_available_personnel(**call.arguments)
            else:
                result = {"error": "Unknown tool"}
                
            function_results.append({
                "type": "function_result",
                "name": call.name,
                "call_id": call.id,
                "result": [{"type": "text", "text": json.dumps(result)}]
            })
        
        # Set tool results as input for the NEXT iteration
        current_input = function_results



