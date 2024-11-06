package com.example.mesh;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public class TopologyTest {
    private static final String API_URL = "http://localhost:8080/generate_topology";
    private static final ObjectMapper mapper = new ObjectMapper();

    @Test
    public void testTopologyGeneration() throws Exception {
        // 生成测试数据
        TestData testData = generateTestData();
        
        // 转换为JSON
        String requestBody = mapper.writeValueAsString(Map.of(
            "nodes_json", mapper.writeValueAsString(testData.nodes),
            "edges_json", mapper.writeValueAsString(testData.edges)
        ));

        // 创建HTTP请求
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL))
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();

        // 创建一个新的 HttpClient
        HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();

        // 发送请求
        HttpResponse<String> response = client.send(request, 
            HttpResponse.BodyHandlers.ofString());

        // 打印格式化的请求和响应信息
        System.out.println("Request body:");
        System.out.println(prettyPrintJson(requestBody));
        System.out.println("\nResponse status: " + response.statusCode());
        System.out.println("Response body:");
        System.out.println(prettyPrintJson(response.body()));

        // 验证响应
        assertEquals(200, response.statusCode(), 
            "Expected status code 200 but got " + response.statusCode() + 
            ". Response body: " + response.body());

        // 验证响应格式
        var responseJson = mapper.readTree(response.body());
        assertTrue(responseJson.has("status"), "Response should have 'status' field");
        assertTrue(responseJson.has("data"), "Response should have 'data' field");
        assertEquals("success", responseJson.get("status").asText(), "Status should be 'success'");
    }

    // 添加用于格式化JSON的辅助方法
    private String prettyPrintJson(String jsonString) {
        try {
            Object json = mapper.readValue(jsonString, Object.class);
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(json);
        } catch (Exception e) {
            return jsonString; // 如果解析失败，返回原始字符串
        }
    }

    private static class TestData {
        public Map<String, NodeInfo> nodes;
        public Map<String, EdgeInfo> edges;
    }

    private static class NodeInfo {
        public List<Double> gps;
        public double load;
        public Map<String, Map<String, List<Integer>>> channels;
        @JsonProperty("max_eirp")
        public Map<String, Map<String, List<Integer>>> maxEirp;

        public NodeInfo() {}
    }

    private static class EdgeInfo {
        public List<Integer> rssi_6gh;
        public List<Integer> rssi_6gl;

        public EdgeInfo() {}
    }

    private EdgeInfo generateEdgeInfo() {
        EdgeInfo edge = new EdgeInfo();
        
        // 首先生成6GL频段的RSSI值（通常信号更强）
        int rssi1_6gl = -40 - (int)(Math.random() * 30); // -40到-70之间
        int rssi2_6gl = rssi1_6gl + (int)(Math.random() * 21 - 10); // 与第一个方向相差-10到+10
        
        // 生成6GH频段的RSSI值（比6GL弱，但差值不超过15）
        int rssi1_6gh = rssi1_6gl - (int)(Math.random() * 16); // 比6GL弱0-15dB
        int rssi2_6gh = rssi2_6gl - (int)(Math.random() * 16); // 比6GL弱0-15dB
        
        // 确保所有RSSI值都在合理范围内（-40到-80之间）
        rssi1_6gh = Math.max(-80, Math.min(-40, rssi1_6gh));
        rssi2_6gh = Math.max(-80, Math.min(-40, rssi2_6gh));
        rssi1_6gl = Math.max(-80, Math.min(-40, rssi1_6gl));
        rssi2_6gl = Math.max(-80, Math.min(-40, rssi2_6gl));
        
        edge.rssi_6gh = Arrays.asList(rssi1_6gh, rssi2_6gh);
        edge.rssi_6gl = Arrays.asList(rssi1_6gl, rssi2_6gl);
        
        return edge;
    }

    private TestData generateTestData() {
        TestData data = new TestData();
        data.nodes = new HashMap<>();
        data.edges = new HashMap<>();

        // 生成节点数据
        for (int i = 0; i < 5; i++) {
            String nodeId = "SN" + i;
            NodeInfo node = new NodeInfo();
            
            // 生成GPS坐标
            node.gps = Arrays.asList(
                30.0 + Math.random(), // 经度
                120.0 + Math.random() // 纬度
            );
            
            // 生成负载
            node.load = Math.random() * 500; // 0-500 Mbps
            
            // 生成信道信息
            node.channels = new HashMap<>();
            node.maxEirp = new HashMap<>();
            
            // 6GH频段
            Map<String, List<Integer>> channels6gh = new HashMap<>();
            Map<String, List<Integer>> eirp6gh = new HashMap<>();
            
            channels6gh.put("160M", Arrays.asList(143));
            channels6gh.put("80M", Arrays.asList(135, 151, 167));
            channels6gh.put("40M", Arrays.asList(123, 131, 139, 147, 155, 163, 171, 179));
            
            eirp6gh.put("160M", Arrays.asList(36));
            eirp6gh.put("80M", Arrays.asList(36, 36, 36));
            eirp6gh.put("40M", Arrays.asList(36, 36, 36, 36, 36, 36, 36, 36));
            
            node.channels.put("6GH", channels6gh);
            node.maxEirp.put("6GH", eirp6gh);
            
            // 6GL频段
            Map<String, List<Integer>> channels6gl = new HashMap<>();
            Map<String, List<Integer>> eirp6gl = new HashMap<>();
            
            channels6gl.put("160M", Arrays.asList(15));
            channels6gl.put("80M", Arrays.asList(7, 23, 39));
            channels6gl.put("40M", Arrays.asList(3, 11, 19, 27, 35, 43, 51, 59));
            channels6gl.put("20M", Arrays.asList(1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61));
            
            eirp6gl.put("160M", Arrays.asList(36));
            eirp6gl.put("80M", Arrays.asList(36, 36, 36));
            eirp6gl.put("40M", Arrays.asList(36, 36, 36, 36, 36, 36, 36, 36));
            eirp6gl.put("20M", Arrays.asList(36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36));
            
            node.channels.put("6GL", channels6gl);
            node.maxEirp.put("6GL", eirp6gl);
            
            data.nodes.put(nodeId, node);
        }

        // 生成边数据
        for (int i = 0; i < 5; i++) {
            for (int j = i + 1; j < 5; j++) {
                String edgeKey = String.format("SN%d_SN%d", i, j);
                data.edges.put(edgeKey, generateEdgeInfo());
            }
        }

        return data;
    }
}
