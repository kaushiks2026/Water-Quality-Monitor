"""
Water Quality Risk Evaluation Logic
===================================
Documented standards and jurisdictional reference:
1. Bureau of Indian Standards (BIS) IS 10500:2012 Drinking Water Specification:
   - pH: Acceptable Limit: 6.5 to 8.5. (No relaxation)
   - Turbidity: Acceptable Limit: 1.0 NTU. Permissible Limit in absence of alternate source: 5.0 NTU.
2. World Health Organization (WHO) Guidelines for Drinking-water Quality (4th ed.):
   - Turbidity: Preferably < 1.0 NTU for effective disinfection. High turbidity protects pathogens.
   - Temperature: High water temperature (> 25°C - 30°C) accelerates microbial growth and reduces dissolved oxygen.
3. Central Pollution Control Board (CPCB) / EPA Surface Water Criteria:
   - Dissolved Oxygen (DO): Healthy aquatic ecosystem >= 6.0 mg/L. Below 4.0 mg/L causes hypoxia / severe stress.

LIMITATION DISCLAIMER:
Monitoring pH, turbidity, temperature, and dissolved oxygen provides an early indicator
of physicochemical anomalies and gross pollution events. It DOES NOT prove water is potable
or free from toxic heavy metals (lead, arsenic), volatile organics, or biological pathogens (E. coli).
"""

from typing import Optional, List, Dict, Any
from backend.app.config import settings


class ParameterEvaluation:
    def __init__(
        self,
        parameter: str,
        value: Optional[float],
        unit: str,
        status: str,  # "NORMAL", "WARNING", "CRITICAL", "NOT_INSTALLED"
        message: str,
        standard_ref: str,
        threshold_info: str
    ):
        self.parameter = parameter
        self.value = value
        self.unit = unit
        self.status = status
        self.message = message
        self.standard_ref = standard_ref
        self.threshold_info = threshold_info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter,
            "value": self.value,
            "unit": self.unit,
            "status": self.status,
            "message": self.message,
            "standard_ref": self.standard_ref,
            "threshold_info": self.threshold_info
        }


def evaluate_water_quality(
    ph: Optional[float],
    turbidity: Optional[float],
    temperature: Optional[float],
    dissolved_oxygen: Optional[float]
) -> Dict[str, Any]:
    """
    Evaluates individual sensor values against documented reference standards,
    classifies overall risk, and generates actionable alerts.
    """
    evaluations: Dict[str, ParameterEvaluation] = {}
    alerts: List[Dict[str, Any]] = []

    # 1. Evaluate pH
    if ph is None:
        evaluations["ph"] = ParameterEvaluation(
            parameter="ph",
            value=None,
            unit="",
            status="NOT_INSTALLED",
            message="pH sensor value unavailable / not installed.",
            standard_ref="BIS 10500:2012",
            threshold_info=f"Acceptable range {settings.PH_MIN} - {settings.PH_MAX}"
        )
    elif ph < settings.PH_MIN:
        severity = "CRITICAL" if ph < 5.0 else "WARNING"
        msg = f"Acidic water detected (pH {ph:.2f}). Below acceptable minimum {settings.PH_MIN}."
        evaluations["ph"] = ParameterEvaluation(
            parameter="ph",
            value=ph,
            unit="",
            status=severity,
            message=msg,
            standard_ref="BIS 10500:2012",
            threshold_info=f"{settings.PH_MIN} - {settings.PH_MAX}"
        )
        alerts.append({
            "parameter": "ph",
            "severity": severity,
            "trigger_value": ph,
            "threshold_limit": f"< {settings.PH_MIN}",
            "message": msg,
            "standard_reference": "BIS 10500:2012 Clause 4"
        })
    elif ph > settings.PH_MAX:
        severity = "CRITICAL" if ph > 9.5 else "WARNING"
        msg = f"Alkaline water detected (pH {ph:.2f}). Exceeds acceptable maximum {settings.PH_MAX}."
        evaluations["ph"] = ParameterEvaluation(
            parameter="ph",
            value=ph,
            unit="",
            status=severity,
            message=msg,
            standard_ref="BIS 10500:2012",
            threshold_info=f"{settings.PH_MIN} - {settings.PH_MAX}"
        )
        alerts.append({
            "parameter": "ph",
            "severity": severity,
            "trigger_value": ph,
            "threshold_limit": f"> {settings.PH_MAX}",
            "message": msg,
            "standard_reference": "BIS 10500:2012 Clause 4"
        })
    else:
        evaluations["ph"] = ParameterEvaluation(
            parameter="ph",
            value=ph,
            unit="",
            status="NORMAL",
            message=f"pH {ph:.2f} is within acceptable limits ({settings.PH_MIN} - {settings.PH_MAX}).",
            standard_ref="BIS 10500:2012",
            threshold_info=f"{settings.PH_MIN} - {settings.PH_MAX}"
        )

    # 2. Evaluate Turbidity
    if turbidity is None:
        evaluations["turbidity"] = ParameterEvaluation(
            parameter="turbidity",
            value=None,
            unit="NTU",
            status="NOT_INSTALLED",
            message="Turbidity sensor value unavailable / not installed.",
            standard_ref="BIS 10500:2012 / WHO",
            threshold_info=f"Acceptable <= {settings.TURBIDITY_WARN} NTU, Max <= {settings.TURBIDITY_MAX} NTU"
        )
    elif turbidity > settings.TURBIDITY_MAX:
        msg = f"Turbidity critical ({turbidity:.2f} NTU). Exceeds maximum permissible limit of {settings.TURBIDITY_MAX} NTU."
        evaluations["turbidity"] = ParameterEvaluation(
            parameter="turbidity",
            value=turbidity,
            unit="NTU",
            status="CRITICAL",
            message=msg,
            standard_ref="BIS 10500:2012 / WHO",
            threshold_info=f"<= {settings.TURBIDITY_MAX} NTU"
        )
        alerts.append({
            "parameter": "turbidity",
            "severity": "CRITICAL",
            "trigger_value": turbidity,
            "threshold_limit": f"> {settings.TURBIDITY_MAX} NTU",
            "message": msg,
            "standard_reference": "BIS 10500:2012 Table 1"
        })
    elif turbidity > settings.TURBIDITY_WARN:
        msg = f"Turbidity elevated ({turbidity:.2f} NTU). Exceeds standard desirable limit of {settings.TURBIDITY_WARN} NTU."
        evaluations["turbidity"] = ParameterEvaluation(
            parameter="turbidity",
            value=turbidity,
            unit="NTU",
            status="WARNING",
            message=msg,
            standard_ref="BIS 10500:2012 / WHO",
            threshold_info=f"<= {settings.TURBIDITY_WARN} NTU"
        )
        alerts.append({
            "parameter": "turbidity",
            "severity": "WARNING",
            "trigger_value": turbidity,
            "threshold_limit": f"> {settings.TURBIDITY_WARN} NTU",
            "message": msg,
            "standard_reference": "BIS 10500:2012 Table 1"
        })
    else:
        evaluations["turbidity"] = ParameterEvaluation(
            parameter="turbidity",
            value=turbidity,
            unit="NTU",
            status="NORMAL",
            message=f"Turbidity {turbidity:.2f} NTU is clear and within desirable limit (<= {settings.TURBIDITY_WARN} NTU).",
            standard_ref="BIS 10500:2012",
            threshold_info=f"<= {settings.TURBIDITY_WARN} NTU"
        )

    # 3. Evaluate Temperature
    if temperature is None:
        evaluations["temperature"] = ParameterEvaluation(
            parameter="temperature",
            value=None,
            unit="°C",
            status="NOT_INSTALLED",
            message="Temperature sensor value unavailable / not installed.",
            standard_ref="WHO Ambient Guidelines",
            threshold_info=f"{settings.TEMP_MIN} - {settings.TEMP_MAX} °C"
        )
    elif temperature < settings.TEMP_MIN or temperature > settings.TEMP_MAX:
        severity = "WARNING"
        msg = f"Water temperature abnormal ({temperature:.1f} °C). Outside normal ambient range ({settings.TEMP_MIN} - {settings.TEMP_MAX} °C)."
        evaluations["temperature"] = ParameterEvaluation(
            parameter="temperature",
            value=temperature,
            unit="°C",
            status=severity,
            message=msg,
            standard_ref="WHO Ambient Guidelines",
            threshold_info=f"{settings.TEMP_MIN} - {settings.TEMP_MAX} °C"
        )
        alerts.append({
            "parameter": "temperature",
            "severity": severity,
            "trigger_value": temperature,
            "threshold_limit": f"{settings.TEMP_MIN} - {settings.TEMP_MAX} °C",
            "message": msg,
            "standard_reference": "Ambient Surface Water Baseline"
        })
    else:
        evaluations["temperature"] = ParameterEvaluation(
            parameter="temperature",
            value=temperature,
            unit="°C",
            status="NORMAL",
            message=f"Temperature {temperature:.1f} °C is normal.",
            standard_ref="WHO Ambient Guidelines",
            threshold_info=f"{settings.TEMP_MIN} - {settings.TEMP_MAX} °C"
        )

    # 4. Evaluate Dissolved Oxygen (DO)
    if dissolved_oxygen is None:
        evaluations["dissolved_oxygen"] = ParameterEvaluation(
            parameter="dissolved_oxygen",
            value=None,
            unit="mg/L",
            status="NOT_INSTALLED",
            message="DO sensor value uninstalled / optional stage.",
            standard_ref="CPCB / EPA Criteria",
            threshold_info=f"Healthy >= {settings.DO_MIN_WARN} mg/L"
        )
    elif dissolved_oxygen < settings.DO_MIN_CRITICAL:
        msg = f"Dissolved oxygen critical hypoxia ({dissolved_oxygen:.2f} mg/L). Below critical limit {settings.DO_MIN_CRITICAL} mg/L."
        evaluations["dissolved_oxygen"] = ParameterEvaluation(
            parameter="dissolved_oxygen",
            value=dissolved_oxygen,
            unit="mg/L",
            status="CRITICAL",
            message=msg,
            standard_ref="CPCB / EPA Surface Water",
            threshold_info=f">= {settings.DO_MIN_CRITICAL} mg/L"
        )
        alerts.append({
            "parameter": "dissolved_oxygen",
            "severity": "CRITICAL",
            "trigger_value": dissolved_oxygen,
            "threshold_limit": f"< {settings.DO_MIN_CRITICAL} mg/L",
            "message": msg,
            "standard_reference": "CPCB Aquatic Class C/D"
        })
    elif dissolved_oxygen < settings.DO_MIN_WARN:
        msg = f"Dissolved oxygen suboptimal ({dissolved_oxygen:.2f} mg/L). Below recommended {settings.DO_MIN_WARN} mg/L."
        evaluations["dissolved_oxygen"] = ParameterEvaluation(
            parameter="dissolved_oxygen",
            value=dissolved_oxygen,
            unit="mg/L",
            status="WARNING",
            message=msg,
            standard_ref="CPCB / EPA Surface Water",
            threshold_info=f">= {settings.DO_MIN_WARN} mg/L"
        )
        alerts.append({
            "parameter": "dissolved_oxygen",
            "severity": "WARNING",
            "trigger_value": dissolved_oxygen,
            "threshold_limit": f"< {settings.DO_MIN_WARN} mg/L",
            "message": msg,
            "standard_reference": "CPCB Aquatic Class C/D"
        })
    else:
        evaluations["dissolved_oxygen"] = ParameterEvaluation(
            parameter="dissolved_oxygen",
            value=dissolved_oxygen,
            unit="mg/L",
            status="NORMAL",
            message=f"Dissolved oxygen {dissolved_oxygen:.2f} mg/L is healthy.",
            standard_ref="CPCB / EPA Criteria",
            threshold_info=f">= {settings.DO_MIN_WARN} mg/L"
        )

    # Determine overall status
    statuses = [ev.status for ev in evaluations.values() if ev.status != "NOT_INSTALLED"]
    if not statuses:
        overall_status = "UNKNOWN"
        summary = "No active sensor readings available to determine water quality risk."
    elif "CRITICAL" in statuses:
        overall_status = "CRITICAL"
        summary = "One or more water quality parameters violate critical safety thresholds!"
    elif "WARNING" in statuses:
        overall_status = "WARNING"
        summary = "One or more water quality parameters exceed desirable advisory limits."
    else:
        overall_status = "SAFE"
        summary = "All installed physicochemical parameters are within acceptable reference boundaries."

    return {
        "overall_status": overall_status,
        "summary_message": summary,
        "parameters_evaluated": {k: v.to_dict() for k, v in evaluations.items()},
        "alerts_generated": alerts
    }
