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
    private static final String API_URL = "http://localhost:1212/generate_topology";
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

        // 发送请求
        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(request, 
            HttpResponse.BodyHandlers.ofString());

        // 打印请求和响应信息用于调试
        System.out.println("Request body: " + requestBody);
        System.out.println("Response status: " + response.statusCode());
        System.out.println("Response body: " + response.body());

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

    private static class TestData {
        Map<String, NodeInfo> nodes;
        Map<String, EdgeInfo> edges;
    }

    private static class NodeInfo {
        List<Double> gps;
        double load;
        Map<String, Map<String, List<Integer>>> channels;
        Map<String, Map<String, List<Integer>>> maxEirp;
    }

    private static class EdgeInfo {
        List<Integer> rssi_6gh;
        List<Integer> rssi_6gl;
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
                EdgeInfo edge = new EdgeInfo();
                
                // 生成RSSI值（-40到-80之间）
                edge.rssi_6gh = Arrays.asList(
                    -40 - (int)(Math.random() * 40),
                    -40 - (int)(Math.random() * 40)
                );
                edge.rssi_6gl = Arrays.asList(
                    -40 - (int)(Math.random() * 40),
                    -40 - (int)(Math.random() * 40)
                );
                
                data.edges.put(edgeKey, edge);
            }
        }

        return data;
    }
}