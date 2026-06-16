import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ActivityIndicator } from "react-native";
import { connectTaskStream } from "../services/websocket";

const LABELS: Record<string, string> = {
  extracting_frames: "Extracting keyframes...",
  detecting_content: "Identifying modules...",
  analyzing_frames: "AI analyzing strokes...",
  retrieving_knowledge: "Searching NTRP guides...",
  generating_report: "Generating report...",
};

export default function AnalysisProgressScreen({ route, navigation }: any) {
  const { taskId } = route.params;
  const [stage, setStage] = useState("queued");
  const [progress, setProgress] = useState(0);
  const [fc, setFc] = useState(0);

  useEffect(() => {
    const ws = connectTaskStream(taskId, (data) => {
      if (data.info) { setStage(data.info.stage || "processing"); setProgress(data.info.progress || 0); if (data.info.frame_count) setFc(data.info.frame_count); }
      if (data.status === "SUCCESS" && data.result?.assessment_id) { ws.close(); navigation.replace("Assessment", { id: data.result.assessment_id }); }
    }, () => {});
    return () => ws.close();
  }, [taskId]);

  return (
    <View style={s.wrap}>
      <Text style={s.title}>AI Analyzing</Text>
      <ActivityIndicator size="large" color="#4CAF50" style={{ marginVertical: 30 }} />
      <Text style={s.stage}>{LABELS[stage] || "Processing..."}</Text>
      <View style={s.bar}><View style={[s.fill, { width: `${Math.round(progress * 100)}%` }]} /></View>
      <Text style={s.pct}>{Math.round(progress * 100)}%</Text>
      {fc > 0 && <Text style={s.detail}>{fc} keyframes extracted</Text>}
      <Text style={s.hint}>Estimated 2-4 minutes</Text>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24, backgroundColor: "#fff" },
  title: { fontSize: 22, fontWeight: "bold" },
  stage: { fontSize: 16, color: "#666", marginBottom: 24 },
  bar: { width: "80%", height: 8, backgroundColor: "#eee", borderRadius: 4, overflow: "hidden" },
  fill: { height: "100%", backgroundColor: "#4CAF50", borderRadius: 4 },
  pct: { marginTop: 8, fontSize: 24, fontWeight: "bold", color: "#4CAF50" },
  detail: { marginTop: 16, fontSize: 14, color: "#999" },
  hint: { marginTop: 32, fontSize: 13, color: "#bbb" },
});
