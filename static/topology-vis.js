class TopologyVisualizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.resize();
        this.scale = 1;
        this.nodeSpacing = 80; // 增加节点间距
        this.levelHeight = 120; // 增加层级高度
        this.nodePadding = 20; // 节点周围的额外空间
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        this.canvas.width = this.canvas.parentElement.clientWidth - 40;
        this.canvas.height = Math.max(600, window.innerHeight - 200);
        if (this.lastData) {
            this.drawTopology(this.lastData);
        }
    }

    drawNode(x, y, node, id) {
        const ctx = this.ctx;
        const radius = 20; // 增加节点大小
        
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = node.backhaulBand === 'H' ? '#f6ad55' : '#63b3ed';
        ctx.fill();
        ctx.strokeStyle = '#2c5282';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        ctx.fillStyle = '#2d3748';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = 'bold 12px Arial';
        ctx.fillText(id, x, y);
        
        ctx.font = '10px Arial';
        const channelInfo = `CH:${node.channel.join(',')}`;
        const bwInfo = `BW:${node.bandwidth.join(',')}`;
        ctx.fillText(channelInfo, x, y + radius + 15);
        ctx.fillText(bwInfo, x, y + radius + 30);
        
        // 添加 GPS 信息显示
        if (node.gps) {
            const gpsInfo = `(${node.gps[0].toFixed(6)}, ${node.gps[1].toFixed(6)})`;
            ctx.fillText(gpsInfo, x, y + radius + 45);
        }
    }

    drawTopology(data) {
        this.lastData = data;
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const root = Object.entries(data).find(([_, node]) => node.parent === null)[0];
        const { positions, width, height } = this.calculateNodePositions(data, root);

        // 计算缩放比例
        const scaleX = this.canvas.width / (width + this.nodePadding * 2);
        const scaleY = this.canvas.height / (height + this.nodePadding * 2);
        this.scale = Math.min(scaleX, scaleY, 1);

        // 应用缩放和平移
        ctx.save();
        ctx.translate(
            (this.canvas.width - width * this.scale) / 2,
            (this.canvas.height - height * this.scale) / 2
        );
        ctx.scale(this.scale, this.scale);

        this.drawConnections(data, positions);
        Object.entries(positions).forEach(([id, pos]) => {
            this.drawNode(pos.x, pos.y, data[id], id);
        });

        ctx.restore();
    }

    calculateNodePositions(data, rootId, x = 0, y = 0) {
        const positions = {};
        const node = data[rootId];
        
        const children = Object.entries(data)
            .filter(([_, n]) => n.parent === rootId)
            .map(([id, _]) => id);

        if (children.length === 0) {
            positions[rootId] = { x, y };
            return { positions, width: this.nodeSpacing, height: this.levelHeight };
        }

        let totalWidth = 0;
        let maxChildHeight = 0;
        let childrenData = children.map(childId => {
            const childResult = this.calculateNodePositions(data, childId, 0, y + this.levelHeight);
            totalWidth += childResult.width;
            maxChildHeight = Math.max(maxChildHeight, childResult.height);
            return { id: childId, ...childResult };
        });

        // 调整子节点的x坐标
        let currentX = x - totalWidth / 2;
        childrenData.forEach(child => {
            const childCenterX = currentX + child.width / 2;
            Object.entries(child.positions).forEach(([id, pos]) => {
                pos.x += childCenterX - x;
                pos.y += this.levelHeight;
            });
            currentX += child.width;
        });

        // 设置当前节点的位置
        positions[rootId] = { x, y };

        // 合并所有子节点的位置
        childrenData.forEach(child => {
            Object.assign(positions, child.positions);
        });

        return {
            positions,
            width: Math.max(totalWidth, this.nodeSpacing),
            height: this.levelHeight + maxChildHeight
        };
    }

    drawConnections(data, positions) {
        const ctx = this.ctx;
        ctx.strokeStyle = '#a0aec0';
        ctx.lineWidth = 2;
        Object.entries(data).forEach(([id, node]) => {
            if (node.parent) {
                const startPos = positions[node.parent];
                const endPos = positions[id];
                ctx.beginPath();
                ctx.moveTo(startPos.x, startPos.y);
                ctx.lineTo(endPos.x, endPos.y);
                ctx.stroke();
            }
        });
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
                    visualizer.drawTopology(result.data.data);
                    activeResult = result;
                };
                
                resultsList.appendChild(div);
            }
        });
        
        // 显示最新的结果
        if (results.length > 0) {
            resultsList.lastChild.click();
        }
    } catch (error) {
        console.error('加载结果失败:', error);
        alert('加载结果失败，请检查网络连接并刷新页面。');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    visualizer = new TopologyVisualizer(document.getElementById('canvas'));
    loadResults();
});