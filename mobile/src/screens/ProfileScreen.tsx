import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { useStore } from "../store/useStore";
import { clearToken } from "../services/auth";

const C = { bg: "#0A0D14", card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", sub: "#9CA3AF", border: "#1F2937" };

export default function ProfileScreen() {
  const user = useStore(s => s.user);
  const setLoggedIn = useStore(s => s.setIsLoggedIn);

  const rows = [
    ["Nickname", user?.nickname || "—"],
    ["Phone", user?.phone || "—"],
    ["Years Playing", user?.playing_years ? `${user.playing_years} yrs` : "—"],
    ["Self Rated", user?.self_rated_ntrp ? `NTRP ${user.self_rated_ntrp}` : "—"],
    ["Target", user?.target_ntrp ? `NTRP ${user.target_ntrp}` : "—"],
    ["Handedness", user?.handedness || "—"],
  ];

  return (
    <ScrollView style={styles.wrap} contentContainerStyle={{ paddingBottom: 40 }}>
      <Text style={styles.title}>Profile</Text>
      <View style={styles.avatar}><Text style={styles.avatarText}>{user?.nickname?.[0]?.toUpperCase() || "P"}</Text></View>
      <View style={styles.card}>
        {rows.map(([label, value], i) => (
          <View key={i} style={[styles.row, i < rows.length - 1 && styles.rowBorder]}>
            <Text style={styles.label}>{label}</Text>
            <Text style={styles.value}>{value}</Text>
          </View>
        ))}
      </View>
      <TouchableOpacity style={styles.logout} onPress={async () => { await clearToken(); setLoggedIn(false); }} activeOpacity={0.7}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, padding: 20 },
  title: { fontSize: 28, fontWeight: "800", color: C.text, marginTop: 50, marginBottom: 24 },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: C.accent, alignItems: "center", justifyContent: "center", alignSelf: "center", marginBottom: 20 },
  avatarText: { fontSize: 28, fontWeight: "700", color: "#0A0D14" },
  card: { backgroundColor: C.card, borderRadius: 16, padding: 4, borderWidth: 1, borderColor: C.border, marginBottom: 24 },
  row: { flexDirection: "row", justifyContent: "space-between", paddingHorizontal: 18, paddingVertical: 14 },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: C.border },
  label: { fontSize: 14, color: C.sub },
  value: { fontSize: 14, fontWeight: "600", color: C.text },
  logout: { backgroundColor: "rgba(239,68,68,0.1)", borderRadius: 14, padding: 16, alignItems: "center", borderWidth: 1, borderColor: "rgba(239,68,68,0.2)" },
  logoutText: { color: "#EF4444", fontSize: 15, fontWeight: "600" },
});
