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
            const response = await fetch('/api/maps/key');
            const { key } = await response.json();
            
            await this.loadGoogleMapsAPI(key);
            
            this.icons = {
                root: {
                    path: 'M20 6c0-1.1-.9-2-2-2h-16c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-12zm-2 0l-8 4.99-8-4.99v-2l8 5 8-5v2zm0 12h-16v-8l8 5 8-5v8z',
                    fillColor: '#FFFFFF',
                    fillOpacity: 1,
                    strokeWeight: 0,
                    scale: 1.5,
                    anchor: new google.maps.Point(10, 10)
                },
                highBand: {
                    path: 'M12 2C7.7 2 3.6 3.4 0.4 6.3L2.5 8.4C5.2 6 8.6 4.8 12 4.8C15.4 4.8 18.8 6 21.5 8.4L23.6 6.3C20.4 3.4 16.3 2 12 2zM12 8C9 8 6.1 9 3.8 10.9L5.9 13C7.7 11.5 9.8 10.8 12 10.8C14.2 10.8 16.3 11.5 18.1 13L20.2 10.9C17.9 9 15 8 12 8zM12 14C10.9 14 10 14.9 10 16C10 17.1 10.9 18 12 18C13.1 18 14 17.1 14 16C14 14.9 13.1 14 12 14z',
                    fillColor: '#3B82F6',
                    fillOpacity: 1,
                    strokeWeight: 0,
                    scale: 1,
                    anchor: new google.maps.Point(12, 12)
                },
                lowBand: {
                    path: 'M12 2C7.7 2 3.6 3.4 0.4 6.3L2.5 8.4C5.2 6 8.6 4.8 12 4.8C15.4 4.8 18.8 6 21.5 8.4L23.6 6.3C20.4 3.4 16.3 2 12 2zM12 8C9 8 6.1 9 3.8 10.9L5.9 13C7.7 11.5 9.8 10.8 12 10.8C14.2 10.8 16.3 11.5 18.1 13L20.2 10.9C17.9 9 15 8 12 8zM12 14C10.9 14 10 14.9 10 16C10 17.1 10.9 18 12 18C13.1 18 14 17.1 14 16C14 14.9 13.1 14 12 14z',
                    fillColor: '#F97316',
                    fillOpacity: 1,
                    strokeWeight: 0,
                    scale: 1,
                    anchor: new google.maps.Point(12, 12)
                }
            };
            
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
        this.markers.forEach(marker => marker.setMap(null));
        this.markers.clear();

        this.polylines.forEach(line => line.setMap(null));
        this.polylines = [];

        this.bounds = new google.maps.LatLngBounds();
    }

    createMarker(nodeId, node) {
        const position = { lat: node.gps[0], lng: node.gps[1] };
        
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

        const infoContent = `
            <div class="bg-white rounded-lg shadow-lg" style="margin: 0; min-width: 200px;">
                <div class="px-4 py-3 border-b border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-800">${nodeId}</h3>
                </div>
                <div class="px-4 py-3">
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div class="text-gray-600">信道</div>
                        <div class="text-gray-900 font-medium">${node.channel.join(',')}</div>
                        <div class="text-gray-600">带宽</div>
                        <div class="text-gray-900 font-medium">${node.bandwidth.join(',')}</div>
                        <div class="text-gray-600">层级</div>
                        <div class="text-gray-900 font-medium">${node.level}</div>
                        <div class="text-gray-600">GPS</div>
                        <div class="text-gray-900 font-medium">${node.gps[0].toFixed(6)}, ${node.gps[1].toFixed(6)}</div>
                    </div>
                </div>
            </div>
        `;

        const infoWindow = new google.maps.InfoWindow({
            content: infoContent,
            disableAutoPan: true,
            pixelOffset: new google.maps.Size(0, -10),
            maxWidth: 300
        });

        google.maps.event.addListener(infoWindow, 'domready', () => {
            document.querySelectorAll('.gm-style-iw-a, .gm-style-iw-t, .gm-style-iw').forEach(el => {
                el.style.background = 'transparent';
                el.style.boxShadow = 'none';
                el.style.border = 'none';
                el.style.padding = '0';
                el.style.borderRadius = '0';
            });
            
            const closeButtons = document.querySelectorAll('.gm-ui-hover-effect');
            closeButtons.forEach(button => button.style.display = 'none');
        });

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

        Object.entries(data).forEach(([nodeId, node]) => {
            const marker = this.createMarker(nodeId, node);
            this.markers.set(nodeId, marker);
        });

        Object.entries(data).forEach(([nodeId, node]) => {
            if (node.parent) {
                this.drawConnection(data[node.parent], node);
            }
        });

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
    await visualizer.init();
    await loadResults();
});