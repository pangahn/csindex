<template>
  <div class="matrix-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>指数成分券矩阵</span>
          <div class="header-controls">
            <el-button-group>
              <el-button
                :type="displayMode === 'weight' ? 'primary' : ''"
                @click="displayMode = 'weight'"
                size="small"
              >
                权重模式
              </el-button>
              <el-button
                :type="displayMode === 'binary' ? 'primary' : ''"
                @click="displayMode = 'binary'"
                size="small"
              >
                二值模式
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-state" v-loading="loading" element-loading-text="正在生成矩阵...">
        <div style="height: 200px;"></div>
      </div>

      <div v-else-if="!matrixData && selectedIndices.length === 0" class="empty-state">
        <el-empty description="请先选择指数并计算重合度">
        </el-empty>
      </div>

      <div v-else-if="!matrixData && selectedIndices.length > 0" class="empty-state">
        <el-empty description="正在加载矩阵数据...">
        </el-empty>
      </div>

      <div v-else class="matrix-content">
        <!-- 矩阵表格 -->
        <div class="matrix-table-wrapper">
          <el-table
            :data="matrixData.indices"
            border
            stripe
            :max-height="maxTableHeight"
            style="width: 100%"
            :row-key="(row, index) => index"
          >
            <!-- 指数信息列 -->
            <el-table-column
              prop="name"
              label="指数名称"
              width="200"
              fixed="left"
              align="left"
              show-overflow-tooltip
            >
              <template #default="scope">
                <div class="index-info">
                  <div class="index-name">{{ getIndexDisplayName(scope.$index) }}（{{ getIndexComponentCount(scope.$index) }}）</div>
                  <div class="index-code">{{ getIndexCode(scope.$index) }}</div>
                </div>
              </template>
            </el-table-column>

            <!-- 动态生成成分券列 -->
            <el-table-column
              v-for="(stock, stockIdx) in matrixData.stocks"
              :key="stock.code"
              :label="stock.name"
              :width="80"
              align="center"
            >
              <template #header>
                <div class="stock-header">
                  <div class="stock-name">{{ stock.name }}</div>
                  <div class="stock-code">{{ stock.code }}</div>
                </div>
              </template>
              <template #default="scope">
                <div
                  class="weight-cell"
                  :class="getWeightCellClass(getWeight(scope.$index, stockIdx))"
                  :style="getWeightCellStyle(getWeight(scope.$index, stockIdx))"
                  :title="formatWeightTooltip(getWeight(scope.$index, stockIdx), scope.row, stock)"
                >
                  <span class="weight-text">{{ formatWeight(getWeight(scope.$index, stockIdx)) }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import api from '@/api/config';

export default {
  name: 'IndexStockMatrix',
  props: {
    selectedIndices: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      loading: false,
      matrixData: null,
      displayMode: 'weight', // 'weight' or 'binary'
      tableHeight: 600
    };
  },
  computed: {
    // 根据指数个数动态计算表格最大高度
    maxTableHeight() {
      if (!this.matrixData || !this.matrixData.indices) {
        return 400; // 默认最大高度
      }

      const indexCount = this.matrixData.indices.length;

      // 如果指数数量较少，让表格自然适应内容高度
      if (indexCount <= 8) {
        return null; // 不设置最大高度限制，让表格自然适应
      }

      // 指数数量较多时，根据指数个数动态计算最大高度
      const baseHeight = 100; // 基础高度（表头等）
      const rowHeight = 42;   // 每行高度
      const maxRows = 12;     // 最多显示的行数，超过则滚动

      const calculatedHeight = baseHeight + (rowHeight * Math.min(indexCount, maxRows));

      // 设置合理的最小和最大高度范围
      return Math.min(Math.max(calculatedHeight, 300), 600);
    }
  },
  methods: {
    async generateMatrix() {
      if (this.selectedIndices.length === 0) {
        this.$message.warning('请先选择指数');
        return;
      }

      this.loading = true;
      try {
        const response = await api.post('/api/index_heatmap', {
          indices: this.selectedIndices
        });

        const data = response.data;

        this.matrixData = {
          indices: data.indices,
          indices_info: data.indices_info, // 新增：包含完整指数信息
          stocks: this.sortStocksByWeight(data.stocks, data.matrix, data.indices_info),
          matrix: data.matrix
        };

        this.$message.success('矩阵生成成功');
      } catch (error) {
        console.error('生成矩阵失败:', error);
        this.$message.error('生成矩阵失败');
      } finally {
        this.loading = false;
      }
    },

    // 新增方法：根据成分券数量最多的指数的权重对股票进行排序
    sortStocksByWeight(stocks, matrix, indicesInfo) {
      if (!stocks || !matrix || !indicesInfo || stocks.length === 0) {
        return stocks;
      }

      // 找到成分券数量最多的指数（第一行）
      let maxComponentIndex = 0;
      let maxComponentCount = 0;

      indicesInfo.forEach((indexInfo, idx) => {
        if (indexInfo.component_count > maxComponentCount) {
          maxComponentCount = indexInfo.component_count;
          maxComponentIndex = idx;
        }
      });

      // 创建股票和权重的映射数组
      const stocksWithWeights = stocks.map((stock, stockIdx) => ({
        ...stock,
        originalIndex: stockIdx,
        weight: matrix[maxComponentIndex] ? (matrix[maxComponentIndex][stockIdx] || 0) : 0
      }));

      // 按权重从大到小排序
      stocksWithWeights.sort((a, b) => b.weight - a.weight);

      // 重新排列matrix数据以匹配新的股票顺序
      this.reorderMatrix(matrix, stocksWithWeights);

      // 返回排序后的股票数组（不包含临时添加的属性）
      // eslint-disable-next-line no-unused-vars
      return stocksWithWeights.map(({ originalIndex, weight, ...stock }) => stock);
    },

    // 重新排列矩阵数据以匹配新的股票顺序
    reorderMatrix(matrix, sortedStocksWithWeights) {
      if (!matrix || !sortedStocksWithWeights) return;

      // 创建新的列顺序映射
      const newColumnOrder = sortedStocksWithWeights.map(stock => stock.originalIndex);

      // 重新排列每一行的数据
      matrix.forEach((row, rowIdx) => {
        if (row) {
          const newRow = newColumnOrder.map(originalIdx => row[originalIdx] || 0);
          matrix[rowIdx] = newRow;
        }
      });
    },

    getWeight(indexIdx, stockIdx) {
      if (!this.matrixData || !this.matrixData.matrix[indexIdx]) return 0;
      return this.matrixData.matrix[indexIdx][stockIdx] || 0;
    },

    formatWeight(weight) {
      if (!weight || weight === 0) return '';

      if (this.displayMode === 'binary') {
        return ''; // 二值模式下不显示文字，只用颜色表示
      } else {
        return weight.toFixed(1);
      }
    },

    getWeightCellStyle(weight) {
      if (!weight || weight === 0) {
        return {
          backgroundColor: '#ffffff',
          color: 'transparent'
        };
      }

      // 获取当前行（指数）的最大权重值，用于归一化
      const maxWeight = this.matrixData ? Math.max(...this.matrixData.matrix.flat()) : 100;
      const ratio = Math.min(weight / maxWeight, 1);

      if (this.displayMode === 'binary') {
        // 二值模式：根据权重决定颜色深浅
        // 基础颜色 (64, 158, 255) - 蓝色
        const baseR = 64;
        const baseG = 158;
        const baseB = 255;

        // 根据权重比例调整颜色深浅
        // 权重越高，颜色越深（RGB值越小）
        // 权重越低，颜色越浅（RGB值越大，趋向白色）
        const minIntensity = 0.3; // 最深颜色的强度
        const intensity = minIntensity + (1 - minIntensity) * (1 - ratio);

        const r = Math.round(baseR + (255 - baseR) * intensity);
        const g = Math.round(baseG + (255 - baseG) * intensity);
        const b = Math.round(baseB + (255 - baseB) * intensity);

        return {
          backgroundColor: `rgb(${r}, ${g}, ${b})`,
          color: ratio > 0.5 ? 'white' : '#333'
        };
      } else {
        // 权重模式：使用连续的颜色映射（colorbar概念）
        return this.getColorFromWeight(ratio);
      }
    },

    // 新增方法：基于权重比例生成连续颜色
    getColorFromWeight(ratio) {
      // 定义颜色渐变：从浅蓝到深蓝再到绿色
      // 使用HSL颜色空间来实现平滑的颜色过渡
      
      let hue, saturation, lightness;
      let textColor;

      if (ratio <= 0.2) {
        // 很低权重：浅蓝色系 (200-220度)
        hue = 210;
        saturation = 30 + ratio * 100; // 30% - 50%
        lightness = 90 - ratio * 200; // 90% - 50%
        textColor = '#666';
      } else if (ratio <= 0.5) {
        // 低到中等权重：蓝色系 (200-240度)
        const localRatio = (ratio - 0.2) / 0.3;
        hue = 210;
        saturation = 50 + localRatio * 30; // 50% - 80%
        lightness = 70 - localRatio * 30; // 70% - 40%
        textColor = localRatio > 0.5 ? 'white' : '#333';
      } else if (ratio <= 0.8) {
        // 中高权重：深蓝到青色 (200-180度)
        const localRatio = (ratio - 0.5) / 0.3;
        hue = 210 - localRatio * 30; // 210度 - 180度
        saturation = 80 + localRatio * 10; // 80% - 90%
        lightness = 40 - localRatio * 10; // 40% - 30%
        textColor = 'white';
      } else {
        // 高权重：青绿色系 (180-120度)
        const localRatio = (ratio - 0.8) / 0.2;
        hue = 180 - localRatio * 60; // 180度 - 120度
        saturation = 90 + localRatio * 10; // 90% - 100%
        lightness = 30 + localRatio * 10; // 30% - 40%
        textColor = 'white';
      }

      return {
        backgroundColor: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
        color: textColor
      };
    },

    formatWeightTooltip(weight, indexName, stock) {
      if (!weight || weight === 0) {
        return `${indexName} 不包含 ${stock.name}(${stock.code})`;
      }
      return `${indexName} 中 ${stock.name}(${stock.code}) 权重: ${weight.toFixed(2)}%`;
    },

    getWeightCellClass(weight) {
      if (!weight || weight === 0) return 'weight-empty';

      if (this.displayMode === 'binary') {
        return 'weight-binary';
      } else {
        // 权重模式：不再使用基于阈值的CSS类，直接返回基础类
        return 'weight-cell-base';
      }
    },

    // 获取指数显示名称
    getIndexDisplayName(indexIdx) {
      if (!this.matrixData || !this.matrixData.indices_info) {
        return this.matrixData?.indices[indexIdx] || '';
      }
      return this.matrixData.indices_info[indexIdx]?.name || '';
    },

    // 获取指数代码
    getIndexCode(indexIdx) {
      if (!this.matrixData || !this.matrixData.indices_info) {
        return '';
      }
      return this.matrixData.indices_info[indexIdx]?.code || '';
    },

    // 获取指数成分券个数
    getIndexComponentCount(indexIdx) {
      if (!this.matrixData || !this.matrixData.indices_info) {
        return 0;
      }
      return this.matrixData.indices_info[indexIdx]?.component_count || 0;
    }
  },

  watch: {
    selectedIndices: {
      handler(newIndices) {
        if (newIndices && newIndices.length > 0) {
          this.generateMatrix();
        } else {
          this.matrixData = null;
        }
      },
      deep: true,
      immediate: true
    }
  }
};
</script>

<style scoped>
.matrix-container {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.matrix-content {
  min-height: 400px;
}

.matrix-table-wrapper {
  overflow-x: auto;
}

.index-info {
  text-align: left;
}

.index-name {
  font-weight: bold;
  color: #303133;
  font-size: 14px;
}

.index-code {
  color: #909399;
  font-size: 12px;
}

.index-count {
  color: #67c23a;
  font-size: 11px;
  font-weight: bold;
}

.stock-header {
  text-align: center;
  line-height: 1.2;
}

.stock-name {
  font-weight: bold;
  color: #303133;
  font-size: 12px;
  margin-bottom: 2px;
}

.stock-code {
  color: #909399;
  font-size: 11px;
}

.weight-cell {
  padding: 0;
  margin: 0;
  border-radius: 0;
  font-weight: bold;
  min-height: 40px;
  height: 40px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.weight-cell:hover {
  transform: scale(1.05);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.weight-text {
  font-size: 12px;
  font-weight: bold;
}

.weight-empty {
  background-color: #ffffff !important;
  color: transparent !important;
}

.weight-binary {
  background-color: #409eff !important;
  color: white !important;
  font-size: 14px;
}

.weight-cell-base {
  /* 基础样式，颜色由内联样式控制 */
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stock-header {
    font-size: 10px;
  }

  .weight-cell {
    min-height: 28px;
    font-size: 11px;
  }
}

/* 表格样式优化 */
:deep(.el-table) {
  font-size: 12px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  padding: 8px 0;
}

:deep(.el-table td) {
  padding: 0;
  border: 1px solid #ebeef5;
}

:deep(.el-table .cell) {
  padding: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 指数名称列左对齐 */
:deep(.el-table td:first-child .cell) {
  justify-content: flex-start;
  padding-left: 12px;
}
</style>