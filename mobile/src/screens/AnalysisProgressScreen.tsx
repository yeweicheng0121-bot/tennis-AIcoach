import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet } from "react-native";
import { connectTaskStream } from "../services/websocket";

const C = { bg: "#0A0D14", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280" };

const LABELS: Record<string, string> = {
  extracting_frames: "Extracting keyframes from video…",
  detecting_content: "Identifying stroke types…",
  analyzing_frames: "AI analyzing your technique…",
  retrieving_knowledge: "Consulting NTRP coaching guides…",
  generating_report: "Writing your assessment report…",
};

export default function AnalysisProgressScreen({ route, navigation }: any) {
  const { taskId } = route.params;
  const [stage, setStage] = useState("queued");
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const ws = connectTaskStream(taskId, (data) => {
      if (data.info) { setStage(data.info.stage || "processing"); setProgress(data.info.progress || 0); }
      if (data.status === "SUCCESS" && data.result?.assessment_id) { ws.close(); navigation.replace("Assessment", { id: data.result.assessment_id }); }
    }, () => {});
    return () => ws.close();
  }, [taskId]);

  return (
    <View style={styles.wrap}>
      <Text style={styles.emoji}>🔍</Text>
      <Text style={styles.title}>Analyzing</Text>
      <Text style={styles.stageText}>{LABELS[stage] || "Processing…"}</Text>

      <View style={styles.barWrap}>
        <View style={styles.bar}><View style={[styles.fill, { width: `${Math.round(progress * 100)}%` }]} /></View>
      </View>
      <Text style={styles.pct}>{Math.round(progress * 100)}%</Text>
      <Text style={styles.hint}>This usually takes 1–3 minutes</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: C.bg, padding: 32 },
  emoji: { fontSize: 48, marginBottom: 16 },
  title: { fontSize: 24, fontWeight: "800", color: C.text, marginBottom: 8 },
  stageText: { fontSize: 15, color: C.muted, marginBottom: 32 },
  barWrap: { width: "85%" },
  bar: { height: 6, backgroundColor: "#1F2937", borderRadius: 3, overflow: "hidden" },
  fill: { height: "100%", backgroundColor: C.accent, borderRadius: 3 },
  pct: { marginTop: 16, fontSize: 40, fontWeight: "800", color: C.accent },
  hint: { marginTop: 40, fontSize: 12, color: C.muted },
});
