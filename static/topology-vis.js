class TopologyVisualizer {
  constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.resize();
      this.scale = 1;
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
      const radius = 15 * this.scale; // 减小节点尺寸
      
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fillStyle = node.backhaulBand === 'H' ? '#f6ad55' : '#63b3ed';
      ctx.fill();
      ctx.strokeStyle = '#2c5282';
      ctx.lineWidth = 1 * this.scale;
      ctx.stroke();
      
      ctx.fillStyle = '#2d3748';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = `bold ${10 * this.scale}px Arial`;
      ctx.fillText(id, x, y);
      
      ctx.font = `${8 * this.scale}px Arial`;
      const channelInfo = `CH:${node.channel.join(',')}`;
      const bwInfo = `BW:${node.bandwidth.join(',')}`;
      ctx.fillText(channelInfo, x, y + radius + 10 * this.scale);
      ctx.fillText(bwInfo, x, y + radius + 20 * this.scale);
  }

  drawTopology(data) {
      this.lastData = data;
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      const root = Object.entries(data).find(([_, node]) => node.parent === null)[0];
      const nodePositions = this.calculateNodePositions(data, root);

      // 计算缩放比例
      const bounds = this.calculateBounds(nodePositions);
      const scaleX = this.canvas.width / (bounds.maxX - bounds.minX + 100);
      const scaleY = this.canvas.height / (bounds.maxY - bounds.minY + 100);
      this.scale = Math.min(scaleX, scaleY, 1); // 限制最大缩放为1

      // 应用缩放和平移
      ctx.save();
      ctx.translate(
          (this.canvas.width - (bounds.maxX - bounds.minX) * this.scale) / 2 - bounds.minX * this.scale,
          (this.canvas.height - (bounds.maxY - bounds.minY) * this.scale) / 2 - bounds.minY * this.scale
      );
      ctx.scale(this.scale, this.scale);

      this.drawConnections(data, nodePositions);
      Object.entries(nodePositions).forEach(([id, pos]) => {
          this.drawNode(pos.x, pos.y, data[id], id);
      });

      ctx.restore();
  }

  calculateNodePositions(data, rootId, x = 0, y = 0, level = 0) {
      const positions = {};
      const node = data[rootId];
      positions[rootId] = { x, y };

      const children = Object.entries(data).filter(([_, n]) => n.parent === rootId);
      if (children.length > 0) {
          const levelWidth = 200; // 调整此值以改变节点之间的水平间距
          const startX = x - (levelWidth * (children.length - 1)) / 2;
          children.forEach(([childId], index) => {
              const childX = startX + levelWidth * index;
              const childY = y + 100; // 调整此值以改变层级之间的垂直间距
              Object.assign(positions, this.calculateNodePositions(data, childId, childX, childY, level + 1));
          });
      }

      return positions;
  }

  calculateBounds(positions) {
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      Object.values(positions).forEach(pos => {
          minX = Math.min(minX, pos.x);
          minY = Math.min(minY, pos.y);
          maxX = Math.max(maxX, pos.x);
          maxY = Math.max(maxY, pos.y);
      });
      return { minX, minY, maxX, maxY };
  }

  drawConnections(data, positions) {
      const ctx = this.ctx;
      Object.entries(data).forEach(([id, node]) => {
          if (node.parent) {
              const startPos = positions[node.parent];
              const endPos = positions[id];
              ctx.beginPath();
              ctx.moveTo(startPos.x, startPos.y);
              ctx.lineTo(endPos.x, endPos.y);
              ctx.strokeStyle = '#a0aec0';
              ctx.lineWidth = 1 * this.scale;
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