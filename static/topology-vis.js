class TopologyVisualizer {
    constructor() {
        this.map = null;
        this.markers = new Map();
        this.polylines = [];
        this.bounds = null;
    }

    async init() {
        // 先从后端获取 API 密钥
        try {
            const response = await fetch('/api/maps/key');
            const { key } = await response.json();
            
            // 动态加载 Google Maps API
            await this.loadGoogleMapsAPI(key);
            
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
        
        // 根据节点类型决定图标颜色
        let color;
        if (node.parent === null) {
            color = '#10B981';
        } else {
            color = node.backhaulBand === 'H' ? '#FB923C' : '#60A5FA';
        }
        
        const marker = new google.maps.Marker({
            position: position,
            map: this.map,
            title: nodeId,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: color,
                fillOpacity: 1,
                strokeColor: '#2c5282',
                strokeWeight: 2,
            }
        });

        // 添加信息窗口
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
            content: infoContent
        });

        marker.addListener('click', () => {
            infoWindow.open(this.map, marker);
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

let visualizer;
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
    loadResults();
});