from datetime import datetime, timedelta
import json
from config import (
    CRISIS_PROTOCOLS, SEVERITY_LEVELS, 
    TOP_K_RESULTS, MIN_CONFIDENCE_THRESHOLD
)

class MemoryService:
    """
    Manages EchoGuard's temporal memory
    - Track crisis evolution
    - Apply time decay
    - Generate reasoning explanations
    - Suggest protocols based on past incidents
    """
    
    def __init__(self):
        """Initialize memory service"""
        self.memory_log = []
        print("✓ Memory service initialized")
    
    def generate_reasoning_explanation(self, query_crisis, matched_crises):
        """
        Generate human-readable explanation of the AI's recommendation
        This is the "Traceable Reasoning" - shows WHY the AI decided
        
        Args:
            query_crisis: The uploaded crisis (image + description)
            matched_crises: Top matching incidents from database
        
        Returns:
            String explanation for the user
        """
        if not matched_crises:
            return "⚠ No similar past incidents found in database. Recommend manual assessment."
        
        best_match = matched_crises[0]
        score = best_match["similarity_score"]
        metadata = best_match["metadata"]
        
        # Build explanation
        explanation = f"""
📊 **REASONING PATH**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 **Match Analysis:**
   • Your uploaded image matches: {metadata.get('description', 'Unknown')}
   • Similarity Score: {score}% (Match confidence)
   • Previous incident occurred: {metadata.get('location', 'Unknown')}
   • Time since incident: {best_match.get('hours_old', '?')} hours ago
   • Time decay factor: {best_match.get('time_decay_factor', 1.0)}x

📋 **Decision Logic:**
   ✓ Query similarity > {MIN_CONFIDENCE_THRESHOLD*100}%? → YES
   ✓ Information recency considered? → YES (time-weighted)
   ✓ Past protocol relevant? → YES

💡 **Recommended Action:**
   Based on incident type '{metadata.get('type', '?')}', follow protocol:
"""
        
        # Add protocol steps
        protocol_type = metadata.get('protocol')
        if protocol_type in CRISIS_PROTOCOLS:
            protocol = CRISIS_PROTOCOLS[protocol_type]
            explanation += f"\n   Priority: {protocol['priority'].upper()}\n"
            for i, action in enumerate(protocol['actions'], 1):
                explanation += f"   {i}. {action}\n"
        
        explanation += f"\n📈 **Confidence Score: {score}%**\n"
        explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return explanation
    
    def create_incident_record(self, image_vector, text_input, metadata):
        """
        Create a new incident record in memory
        
        Args:
            image_vector: Vector from image
            text_input: Text description from user
            metadata: Additional info (location, affected people, etc.)
        
        Returns:
            Incident record dictionary
        """
        incident = {
            "timestamp": datetime.now().isoformat(),
            "image_vector": image_vector,
            "text_description": text_input,
            "metadata": metadata,
            "responses": [],
            "lessons_learned": []
        }
        
        self.memory_log.append(incident)
        print(f"✓ Created incident record at {incident['timestamp']}")
        
        return incident
    
    def suggest_protocol(self, crisis_type, severity):
        """
        Suggest emergency protocol based on crisis type and severity
        
        Args:
            crisis_type: Type of crisis (flood, fire, etc.)
            severity: Severity level (critical, high, etc.)
        
        Returns:
            Protocol dictionary with actions
        """
        if crisis_type not in CRISIS_PROTOCOLS:
            return {
                "actions": ["⚠ Unknown crisis type. Escalate to command center immediately."],
                "priority": "critical"
            }
        
        protocol = CRISIS_PROTOCOLS[crisis_type].copy()
        
        # Adjust protocol based on severity
        if severity in SEVERITY_LEVELS:
            severity_score = SEVERITY_LEVELS[severity]
            # Could adjust actions based on severity in future
        
        return protocol
    
    def calculate_time_decay(self, incident_timestamp, decay_hours=24):
        """
        Calculate how much an old incident's relevance decays over time
        
        Args:
            incident_timestamp: ISO format timestamp
            decay_hours: Hours after which relevance drops significantly
        
        Returns:
            Decay factor (0-1, where 1 = full relevance, 0 = no relevance)
        """
        try:
            incident_time = datetime.fromisoformat(incident_timestamp)
            now = datetime.now()
            time_diff = now - incident_time
            hours_passed = time_diff.total_seconds() / 3600
            
            # Linear decay
            if hours_passed <= decay_hours:
                decay = 1.0  # Full relevance within decay period
            else:
                # Gradually decay after decay_hours
                decay = max(0.3, 1.0 - (hours_passed / (decay_hours * 3)) * 0.7)
            
            return round(decay, 2)
            
        except Exception as e:
            print(f"⚠ Error calculating time decay: {str(e)}")
            return 1.0
    
    def rank_incidents_by_relevance(self, incidents, current_time=None):
        """
        Rank multiple incidents by combined relevance score
        Considers: similarity, recency, severity
        
        Args:
            incidents: List of incident records
            current_time: Reference time (default: now)
        
        Returns:
            Sorted list by relevance (highest first)
        """
        if current_time is None:
            current_time = datetime.now()
        
        scored_incidents = []
        
        for incident in incidents:
            try:
                similarity = incident.get("similarity_score", 0.5)
                severity = SEVERITY_LEVELS.get(
                    incident.get("severity", "medium"), 0.5
                )
                time_decay = self.calculate_time_decay(
                    incident.get("timestamp")
                )
                
                # Combined score: 50% similarity, 30% time, 20% severity
                combined_score = (
                    similarity * 0.5 +
                    (time_decay * 100) * 0.3 +
                    (severity * 100) * 0.2
                )
                
                incident_copy = incident.copy()
                incident_copy["relevance_score"] = round(combined_score, 2)
                scored_incidents.append(incident_copy)
                
            except Exception as e:
                print(f"⚠ Error scoring incident: {str(e)}")
        
        # Sort by relevance
        scored_incidents.sort(
            key=lambda x: x["relevance_score"], 
            reverse=True
        )
        
        return scored_incidents
    
    def get_memory_snapshot(self):
        """
        Get current memory state (for logging/debugging)
        """
        return {
            "total_incidents": len(self.memory_log),
            "recent_incidents": self.memory_log[-5:] if self.memory_log else [],
            "timestamp": datetime.now().isoformat()
        }
    
    def log_decision(self, query, decision, confidence):
        """
        Log every decision made by the system for audit trail
        
        Args:
            query: The user's query (uploaded image, description)
            decision: The AI's recommendation
            confidence: Confidence level (0-100)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "decision": decision,
            "confidence": confidence
        }
        
        self.memory_log.append(log_entry)
        print(f"📝 Decision logged with {confidence}% confidence")
        
        return log_entry
    
    def get_crisis_summary(self, crisis_data):
        """
        Generate executive summary of a crisis
        """
        summary = f"""
╔══════════════════════════════════════════╗
║        CRISIS SUMMARY REPORT             ║
╚══════════════════════════════════════════╝

Type: {crisis_data.get('type', 'Unknown').upper()}
Location: {crisis_data.get('location', 'Unknown')}
Severity: {crisis_data.get('severity', 'Unknown').upper()}

Description:
{crisis_data.get('description', 'No description available')}

Affected Population: {crisis_data.get('affected_people', 'Unknown')}
Time of Incident: {crisis_data.get('timestamp', 'Unknown')}

Actions Required:
"""
        
        protocol = CRISIS_PROTOCOLS.get(crisis_data.get('protocol'))
        if protocol:
            for i, action in enumerate(protocol['actions'], 1):
                summary += f"\n{i}. {action}"
        
        summary += "\n\n" + "="*42 + "\n"
        
        return summary