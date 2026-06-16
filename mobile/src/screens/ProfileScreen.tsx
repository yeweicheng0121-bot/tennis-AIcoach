import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { useStore } from "../store/useStore";
import { clearToken } from "../services/auth";

export default function ProfileScreen() {
  const user = useStore(s => s.user);
  const setLoggedIn = useStore(s => s.setIsLoggedIn);

  return (
    <View style={s.wrap}>
      <Text style={s.title}>Profile</Text>
      <View style={s.sec}>
        <Text style={s.lbl}>Nickname: {user?.nickname || "-"}</Text>
        <Text style={s.lbl}>Years: {user?.playing_years || "-"}</Text>
        <Text style={s.lbl}>Self: NTRP {user?.self_rated_ntrp || "-"}</Text>
        <Text style={s.lbl}>Target: NTRP {user?.target_ntrp || "-"}</Text>
      </View>
      <TouchableOpacity style={s.logout} onPress={async () => { await clearToken(); setLoggedIn(false); }}>
        <Text style={s.logoutT}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  title: { fontSize: 22, fontWeight: "bold", marginTop: 40, marginBottom: 20 },
  sec: { backgroundColor: "#fff", borderRadius: 12, padding: 16, marginBottom: 16 },
  lbl: { fontSize: 16, marginVertical: 4, color: "#333" },
  logout: { backgroundColor: "#ff4444", borderRadius: 12, padding: 16, alignItems: "center" },
  logoutT: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
