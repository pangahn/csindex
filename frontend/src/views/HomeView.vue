<template>
  <div class="home-container">
    <el-row :gutter="20">
      <!-- 第一部分：指数候选列表 -->
      <el-col :span="8">
        <el-card class="index-card">
          <template #header>
            <div class="card-header">
              <span>指数候选列表</span>
              <div>
                <el-radio-group v-model="currentProvider" @change="changeProvider">
                  <el-radio-button v-for="provider in providers" :key="provider.id" :label="provider.id">
                    {{ provider.name }}
                  </el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="search-container">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索指数代码或名称..."
              prefix-icon="el-icon-search"
              clearable
              @input="handleSearch"
              style="margin-bottom: 15px;"
            />

            <!-- 批量导入功能 -->
            <el-collapse v-model="batchImportCollapse" style="margin-bottom: 15px;">
              <el-collapse-item title="批量导入指数代码" name="1">
                <el-input
                  v-model="batchImportText"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入指数代码，每行一个代码，例如：&#10;000001&#10;000002&#10;000300"
                  style="margin-bottom: 10px;"
                />
                <div class="batch-import-actions">
                  <el-button
                    type="primary"
                    @click="parseBatchImport"
                    :disabled="!batchImportText.trim()"
                  >
                    解析代码
                  </el-button>
                  <el-button
                    type="success"
                    @click="importAllMatched"
                    :disabled="matchedIndices.length === 0"
                  >
                    全部导入 ({{ matchedIndices.length }})
                  </el-button>
                  <el-button
                    type="info"
                    @click="clearBatchImport"
                    :disabled="!batchImportText.trim() && matchedIndices.length === 0"
                  >
                    清空
                  </el-button>
                </div>

                <!-- 匹配结果展示 -->
                <div v-if="matchedIndices.length > 0" class="matched-results">
                  <el-divider content-position="left">找到的指数 ({{ matchedIndices.length }})</el-divider>
                  <el-table
                    :data="matchedIndices"
                    style="width: 100%"
                    max-height="200"
                    size="small"
                  >
                    <el-table-column prop="指数代码" label="指数代码" width="120" />
                    <el-table-column prop="指数简称" label="指数简称" />
                    <el-table-column fixed="right" label="操作" width="80">
                      <template #default="scope">
                        <el-button type="primary" size="small" @click="addToSelected(scope.row)">
                          添加
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>

                <!-- 未找到的代码展示 -->
                <div v-if="unmatchedCodes.length > 0" class="unmatched-results">
                  <el-divider content-position="left">未找到的代码 ({{ unmatchedCodes.length }})</el-divider>
                  <el-tag
                    v-for="code in unmatchedCodes"
                    :key="code"
                    type="warning"
                    style="margin: 2px;"
                  >
                    {{ code }}
                  </el-tag>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
          <div class="index-list">
            <el-table
              v-loading="loading.indices"
              :data="filteredIndices"
              style="width: 100%"
              height="400"
              @row-click="handleSelectIndex"
            >
              <el-table-column prop="指数代码" label="指数代码" width="120" />
              <el-table-column prop="指数简称" label="指数简称" />
              <el-table-column fixed="right" label="操作" width="100">
                <template #default="scope">
                  <el-button type="primary" size="small" @click.stop="addToSelected(scope.row)">
                    添加
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>

      <!-- 第二部分：选定的指数列表 -->
      <el-col :span="8">
        <el-card class="index-card">
          <template #header>
            <div class="card-header">
              <span>选定的指数列表</span>
              <div>
                <el-button type="danger" size="small" :disabled="selectedIndices.length === 0" @click="clearSelected" style="margin-right: 10px;">
                  清空
                </el-button>
                <el-button type="primary" :disabled="selectedIndices.length < 2" @click="calculateOverlap">
                  计算重合度
                </el-button>
              </div>
            </div>
          </template>
          <div class="selected-list">
            <el-table
              :data="selectedIndices"
              style="width: 100%; height: 100%;"
              height="480"
              @row-click="showComponents"
            >
              <el-table-column prop="code" label="指数代码" width="120" />
              <el-table-column prop="name" label="指数简称" />
              <el-table-column prop="source" label="来源">
                <template #default="scope">
                  {{ scope.row.source === 'cs' ? '中证指数' : '国证指数' }}
                </template>
              </el-table-column>
              <el-table-column fixed="right" label="操作" width="100">
                <template #default="scope">
                  <el-button type="danger" size="small" @click.stop="removeFromSelected(scope.$index)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>

      <!-- 第三部分：指数成分列表 -->
      <el-col :span="8">
        <el-card class="index-card">
          <template #header>
            <div class="card-header">
              <span>{{ currentComponents.length > 0 ? currentComponentsTitle : '指数成分列表' }}</span>
            </div>
          </template>
          <div v-if="currentComponents.length === 0" class="empty-components">
            <el-empty description="点击左侧指数查看成分列表" />
          </div>
          <el-table
            v-else
            v-loading="loading.components"
            :data="currentComponents"
            style="width: 100%"
            height="480"
          >
            <el-table-column prop="成分券代码" label="成分券代码" width="120" />
            <el-table-column prop="成分券简称" label="成分券简称" />
            <el-table-column prop="权重" label="权重" width="120">
              <template #default="scope">
                {{ scope.row.权重 ? (scope.row.权重 + '%') : '-' }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第四部分：可视化结果 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <!-- 指数成分券矩阵 -->
        <IndexStockMatrix
          :selected-indices="selectedIndices"
        />

        <!-- 重合度分析 -->
        <OverlapAnalysis
          ref="overlapAnalysis"
          :selected-indices="selectedIndices"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script>
import api from '@/api/config';
import IndexStockMatrix from '@/components/IndexStockMatrix.vue';
import OverlapAnalysis from '@/components/OverlapAnalysis.vue';

export default {
  name: 'HomeView',
  components: {
    IndexStockMatrix,
    OverlapAnalysis
  },
  data() {
    return {
      providers: [],
      currentProvider: 'cs',
      indices: [],
      searchKeyword: '',
      selectedIndices: [],
      currentComponents: [],
      currentComponentsTitle: '',
      loading: {
        indices: false,
        components: false
      },
      // 批量导入相关数据
      batchImportCollapse: [],
      batchImportText: '',
      matchedIndices: [],
      unmatchedCodes: []
    };
  },
  created() {
    this.fetchProviders();
  },
  computed: {
    filteredIndices() {
      if (!this.searchKeyword) {
        return this.indices;
      }

      const keyword = this.searchKeyword.toLowerCase();
      return this.indices.filter(index => {
        const code = (index.指数代码 || '').toLowerCase();
        const name = (index.指数简称 || '').toLowerCase();
        return code.includes(keyword) || name.includes(keyword);
      });
    }
  },
  methods: {
    async fetchProviders() {
       try {
         const response = await api.get('/api/index_providers');
         this.providers = response.data;
         this.fetchIndices(this.currentProvider);
       } catch (error) {
         console.error('获取指数提供商失败:', error);
         this.$message.error('获取指数提供商失败');
       }
     },
     async fetchIndices(provider) {
       this.loading.indices = true;
       try {
         const response = await api.get(`/api/indices/${provider}`);
         this.indices = response.data;
       } catch (error) {
         console.error('获取指数列表失败:', error);
         this.$message.error('获取指数列表失败');
       } finally {
         this.loading.indices = false;
       }
     },
    changeProvider(provider) {
       this.fetchIndices(provider);
     },
     handleSearch() {
       // 搜索功能通过computed属性filteredIndices自动实现
       // 这里可以添加额外的搜索逻辑，比如防抖等
     },
    handleSelectIndex(row) {
      this.addToSelected(row);
    },
    addToSelected(row) {
      const index = {
        code: row.指数代码,
        name: row.指数简称,
        source: this.currentProvider
      };

      // 检查是否已经添加过
      const exists = this.selectedIndices.some(item =>
        item.code === index.code && item.source === index.source
      );

      if (!exists) {
        this.selectedIndices.push(index);
        this.$message.success(`已添加: ${index.name}`);
      } else {
        this.$message.warning('该指数已在选定列表中');
      }
    },
    removeFromSelected(index) {
      this.selectedIndices.splice(index, 1);
    },
    clearSelected() {
      this.selectedIndices = [];
      this.$message.success('已清空选定的指数列表');
    },
    async showComponents(row) {
      this.loading.components = true;
      this.currentComponentsTitle = `${row.name} (${row.code}) 成分列表`;

      try {
         const response = await api.get('/api/index_components', {
           params: {
             code: row.code,
             source: row.source
           }
         });
         this.currentComponents = response.data;
       } catch (error) {
         console.error('获取指数成分失败:', error);
         this.$message.error('获取指数成分失败');
         this.currentComponents = [];
       } finally {
         this.loading.components = false;
       }
     },
    async calculateOverlap() {
      if (this.selectedIndices.length < 2) {
        this.$message.warning('请至少选择两个指数进行计算');
        return;
      }

      // 调用子组件的计算方法
      this.$refs.overlapAnalysis.calculateOverlap();
    },
    // 批量导入相关方法
    parseBatchImport() {
      if (!this.batchImportText.trim()) {
        this.$message.warning('请输入指数代码');
        return;
      }

      // 解析输入的代码，每行一个
      const inputCodes = this.batchImportText
        .split('\n')
        .map(code => code.trim())
        .filter(code => code.length > 0);

      if (inputCodes.length === 0) {
        this.$message.warning('请输入有效的指数代码');
        return;
      }

      // 在当前指数列表中查找匹配的指数
      this.matchedIndices = [];
      this.unmatchedCodes = [];

      inputCodes.forEach(code => {
        const matchedIndex = this.indices.find(index =>
          index.指数代码 === code || index.指数代码 === code.padStart(6, '0')
        );

        if (matchedIndex) {
          // 检查是否已经在匹配列表中
          const alreadyMatched = this.matchedIndices.some(item =>
            item.指数代码 === matchedIndex.指数代码
          );
          if (!alreadyMatched) {
            this.matchedIndices.push(matchedIndex);
          }
        } else {
          this.unmatchedCodes.push(code);
        }
      });

      // 显示解析结果
      if (this.matchedIndices.length > 0) {
        this.$message.success(`找到 ${this.matchedIndices.length} 个匹配的指数`);
      }
      if (this.unmatchedCodes.length > 0) {
        this.$message.warning(`有 ${this.unmatchedCodes.length} 个代码未找到匹配的指数`);
      }
    },

    importAllMatched() {
      if (this.matchedIndices.length === 0) {
        this.$message.warning('没有可导入的指数');
        return;
      }

      let successCount = 0;
      let duplicateCount = 0;

      this.matchedIndices.forEach(row => {
        const index = {
          code: row.指数代码,
          name: row.指数简称,
          source: this.currentProvider
        };

        // 检查是否已经添加过
        const exists = this.selectedIndices.some(item =>
          item.code === index.code && item.source === index.source
        );

        if (!exists) {
          this.selectedIndices.push(index);
          successCount++;
        } else {
          duplicateCount++;
        }
      });

      // 显示导入结果
      if (successCount > 0) {
        this.$message.success(`成功导入 ${successCount} 个指数`);
      }
      if (duplicateCount > 0) {
        this.$message.info(`跳过 ${duplicateCount} 个已存在的指数`);
      }

      // 清空批量导入数据
      this.clearBatchImport();
    },

    clearBatchImport() {
      this.batchImportText = '';
      this.matchedIndices = [];
      this.unmatchedCodes = [];
      this.batchImportCollapse = [];
    }
  }
};
</script>

<style scoped>

.search-container {
  padding: 0 20px;
}

.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.index-card {
  height: 100%;
}

.index-card .el-card__body {
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
}

.selected-list {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-components {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 480px;
}

.batch-import-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.matched-results, .unmatched-results {
  margin-top: 15px;
}

.unmatched-results .el-tag {
  margin: 2px 4px 2px 0;
}
</style>