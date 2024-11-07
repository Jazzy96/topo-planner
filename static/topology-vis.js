class TopologyVisualizer {
    constructor() {
        this.map = null;
        this.markers = new Map();
        this.polylines = [];
        this.bounds = null;
        this.icons = null;
    }

    async init() {
        try {
            // 先从后端获取 API 密钥
            const response = await fetch('/api/maps/key');
            const { key } = await response.json();
            
            // 动态加载 Google Maps API
            await this.loadGoogleMapsAPI(key);
            
            // 初始化图标 (现在可以安全地使用 google.maps)
            this.icons = {
                root: {
                    path: 'M12,2C7.79,2,3.7,4.41,2.46,7.47L4,9C4.96,6.67,8.28,4.5,12,4.5s7.04,2.17,8,4.5l1.54-1.53 C20.3,4.41,16.21,2,12,2z M12,8C9.67,8,7.15,9.53,6.34,11.6l1.41,1.41C8.37,11.7,10.32,10.5,12,10.5s3.63,1.2,4.25,2.51l1.41-1.41 C16.85,9.53,14.33,8,12,8z M12,14c-1.38,0-2.63,0.56-3.54,1.46L12,19l3.54-3.54C14.63,14.56,13.38,14,12,14z',
                    fillColor: '#FFFFFF',
                    fillOpacity: 1,
                    strokeColor: '#000000',
                    strokeWeight: 1,
                    scale: 1.2,
                    anchor: new google.maps.Point(12, 12)
                },
                highBand: {
                    path: 'M12,2C7.79,2,3.7,4.41,2.46,7.47L4,9C4.96,6.67,8.28,4.5,12,4.5s7.04,2.17,8,4.5l1.54-1.53 C20.3,4.41,16.21,2,12,2z M12,8C9.67,8,7.15,9.53,6.34,11.6l1.41,1.41C8.37,11.7,10.32,10.5,12,10.5s3.63,1.2,4.25,2.51l1.41-1.41 C16.85,9.53,14.33,8,12,8z',
                    fillColor: '#3B82F6',
                    fillOpacity: 1,
                    strokeColor: '#1E40AF',
                    strokeWeight: 1,
                    scale: 1,
                    anchor: new google.maps.Point(12, 12)
                },
                lowBand: {
                    path: 'M12,2C7.79,2,3.7,4.41,2.46,7.47L4,9C4.96,6.67,8.28,4.5,12,4.5s7.04,2.17,8,4.5l1.54-1.53 C20.3,4.41,16.21,2,12,2z M12,8C9.67,8,7.15,9.53,6.34,11.6l1.41,1.41C8.37,11.7,10.32,10.5,12,10.5s3.63,1.2,4.25,2.51l1.41-1.41 C16.85,9.53,14.33,8,12,8z',
                    fillColor: '#F97316',
                    fillOpacity: 1,
                    strokeColor: '#C2410C',
                    strokeWeight: 1,
                    scale: 1,
                    anchor: new google.maps.Point(12, 12)
                }
            };
            
            // 初始化地图相关对象
            this.bounds = new google.maps.LatLngBounds();
            this.initMap();
        } catch (error) {
            console.error('初始化地图失败:', error);
            alert('初始化地图失败，请刷新页面重试');
        }
    }

    loadGoogleMapsAPI(key) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${key}`;
            script.async = true;
            script.defer = true;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    initMap() {
        this.map = new google.maps.Map(document.getElementById('map'), {
            zoom: 15,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        });
    }

    clearMap() {
        // 清除所有标记
        this.markers.forEach(marker => marker.setMap(null));
        this.markers.clear();

        // 清除所有连线
        this.polylines.forEach(line => line.setMap(null));
        this.polylines = [];

        // 重置边界
        this.bounds = new google.maps.LatLngBounds();
    }

    createMarker(nodeId, node) {
        const position = { lat: node.gps[0], lng: node.gps[1] };
        
        // 根据节点类型选择图标
        let icon;
        if (node.parent === null) {
            icon = this.icons.root;
        } else {
            icon = node.backhaulBand === 'H' ? this.icons.highBand : this.icons.lowBand;
        }
        
        const marker = new google.maps.Marker({
            position: position,
            map: this.map,
            title: nodeId,
            icon: icon
        });

        // 创建信息窗口
        const infoContent = `
            <div class="p-2">
                <h3 class="font-bold">${nodeId}</h3>
                <p>信道: ${node.channel.join(',')}</p>
                <p>带宽: ${node.bandwidth.join(',')}</p>
                <p>层级: ${node.level}</p>
                <p>GPS: ${node.gps[0]}, ${node.gps[1]}</p>
            </div>
        `;

        const infoWindow = new google.maps.InfoWindow({
            content: infoContent,
            disableAutoPan: true // 防止地图自动平移
        });

        // 添加鼠标悬停事件
        marker.addListener('mouseover', () => {
            infoWindow.open(this.map, marker);
        });

        marker.addListener('mouseout', () => {
            infoWindow.close();
        });

        this.bounds.extend(position);
        return marker;
    }

    drawConnection(fromNode, toNode) {
        const line = new google.maps.Polyline({
            path: [
                { lat: fromNode.gps[0], lng: fromNode.gps[1] },
                { lat: toNode.gps[0], lng: toNode.gps[1] }
            ],
            geodesic: true,
            strokeColor: '#a0aec0',
            strokeOpacity: 1.0,
            strokeWeight: 2,
            map: this.map
        });
        
        this.polylines.push(line);
    }

    visualizeTopology(data) {
        this.clearMap();

        // 创建所有节点的标记
        Object.entries(data).forEach(([nodeId, node]) => {
            const marker = this.createMarker(nodeId, node);
            this.markers.set(nodeId, marker);
        });

        // 绘制连接线
        Object.entries(data).forEach(([nodeId, node]) => {
            if (node.parent) {
                this.drawConnection(data[node.parent], node);
            }
        });

        // 调整地图视野以显示所有节点
        this.map.fitBounds(this.bounds);
    }
}

let visualizer = null;
let activeResult = null;

async function loadResults() {
    try {
        const response = await fetch('/api/results');
        const results = await response.json();
        
        const resultsList = document.getElementById('resultsList');
        resultsList.innerHTML = '';
        
        results.forEach(result => {
            const div = document.createElement('div');
            div.className = 'result-item p-3 rounded cursor-pointer';
            const filename = result.filename;
            const matches = filename.match(/topology_(\d+)nodes_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.json/);
            if (matches) {
                const [_, nodeCount, year, month, day, hour, minute, second] = matches;
                const date = new Date(year, month - 1, day, hour, minute, second);
                div.innerHTML = `
                    <div class="font-semibold">${nodeCount} 节点</div>
                    <div class="text-sm text-gray-600">${date.toLocaleString()}</div>
                `;
                
                div.onclick = () => {
                    document.querySelectorAll('.result-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    div.classList.add('active');
                    visualizer.visualizeTopology(result.data.data);
                    activeResult = result;
                };
                
                resultsList.appendChild(div);
            }
        });
        
        // 显示第一个结果（最新的）
        if (results.length > 0) {
            resultsList.firstChild.click();
        }
    } catch (error) {
        console.error('加载结果失败:', error);
        alert('加载结果失败，请检查网络连接并刷新页面。');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    visualizer = new TopologyVisualizer();
    await visualizer.init();  // 等待初始化完成
    await loadResults();  // 也建议等待结果加载完成
});