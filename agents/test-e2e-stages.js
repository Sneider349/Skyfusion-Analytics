'use strict';

const { orchestrator, PIPELINE_STAGES, STAGE_STATUS } = require('./orchestrator');

async function testStage1_PolygonLoad() {
  console.log('\n' + '='.repeat(60));
  console.log('TEST 1: POLYGON_LOAD - Cargar el polígono');
  console.log('='.repeat(60));
  
  const polygonData = {
    id: 'test_basin_01',
    name: 'Cuenca Test Ibagué',
    coordinates: [
      [-75.1847, 4.4378],
      [-75.1247, 4.4378],
      [-75.1247, 4.4978],
      [-75.1847, 4.4978],
      [-75.1847, 4.4378]
    ],
    river: 'Río Test',
    municipality: 'Ibagué'
  };

  try {
    const result = await orchestrator.executeE2EPipeline(polygonData, { pipelineId: 'test_polygon' });
    const stage = result.stages[Object.keys(PIPELINE_STAGES)[0]];
    
    console.log('\n📋 Resultado:');
    console.log('  - Estado:', stage.status);
    console.log('  - Polígono cargado:', stage.data?.polygon?.name || 'N/A');
    console.log('  - Bounds:', JSON.stringify(stage.data?.bounds));
    console.log('  - Timestamp:', stage.data?.loadedAt);
    
    if (stage.status === 'COMPLETED') {
      console.log('\n✅ TEST 1 PASÓ: El polígono se cargó correctamente');
    } else {
      console.log('\n❌ TEST 1 FALLÓ:', stage.error);
    }
    
    return stage.status === 'COMPLETED';
  } catch (error) {
    console.log('\n❌ TEST 1 ERROR:', error.message);
    return false;
  }
}

async function testStage2_GEEIngest() {
  console.log('\n' + '='.repeat(60));
  console.log('TEST 2: GEE_INGEST - Ingestar datos de Google Earth Engine');
  console.log('='.repeat(60));

  const polygonData = {
    id: 'test_basin_02',
    name: 'Cuenca Test GEE',
    coordinates: [
      [-75.1847, 4.4378],
      [-75.1247, 4.4378],
      [-75.1247, 4.4978],
      [-75.1847, 4.4978],
      [-75.1847, 4.4378]
    ]
  };

  try {
    const result = await orchestrator.executeE2EPipeline(polygonData, { pipelineId: 'test_gee' });
    const stage = result.stages[Object.keys(PIPELINE_STAGES)[1]];
    
    console.log('\n📋 Resultado:');
    console.log('  - Estado:', stage.status);
    console.log('  - Records obtenidos:', stage.data?.recordsCount);
    console.log('  - Datos:', JSON.stringify(stage.data?.data?.slice(0, 2)));
    console.log('  - Timestamp:', stage.data?.ingestedAt);
    
    if (stage.status === 'COMPLETED') {
      console.log('\n✅ TEST 2 PASÓ: Datos GEE ingestados correctamente');
    } else {
      console.log('\n❌ TEST 2 FALLÓ:', stage.error);
    }
    
    return stage.status === 'COMPLETED';
  } catch (error) {
    console.log('\n❌ TEST 2 ERROR:', error.message);
    return false;
  }
}

async function testStage3_VisionProcess() {
  console.log('\n' + '='.repeat(60));
  console.log('TEST 3: VISION_PROCESS - Procesar Visión (NDVI, NDWI, Morfológico)');
  console.log('='.repeat(60));

  const polygonData = {
    id: 'test_basin_03',
    name: 'Cuenca Test Visión',
    coordinates: [
      [-75.1847, 4.4378],
      [-75.1247, 4.4378],
      [-75.1247, 4.4978],
      [-75.1847, 4.4978],
      [-75.1847, 4.4378]
    ]
  };

  try {
    const result = await orchestrator.executeE2EPipeline(polygonData, { pipelineId: 'test_vision' });
    const stage = result.stages[Object.keys(PIPELINE_STAGES)[2]];
    
    console.log('\n📋 Resultado:');
    console.log('  - Estado:', stage.status);
    
    if (stage.data?.results) {
      console.log('  - NDVI:', stage.data.results.ndvi?.isFallback ? 'Fallback' : 'Real');
      console.log('  - NDWI:', stage.data.results.ndwi?.isFallback ? 'Fallback' : 'Real');
      console.log('  - MORPHOLOGICAL:', stage.data.results.morphological?.isFallback ? 'Fallback' : 'Real');
    }
    
    console.log('  - Timestamp:', stage.data?.processedAt);
    
    if (stage.status === 'COMPLETED') {
      console.log('\n✅ TEST 3 PASÓ: Procesamiento de visión completado');
    } else {
      console.log('\n❌ TEST 3 FALLÓ:', stage.error);
    }
    
    return stage.status === 'COMPLETED';
  } catch (error) {
    console.log('\n❌ TEST 3 ERROR:', error.message);
    return false;
  }
}

async function testStage4_Predict() {
  console.log('\n' + '='.repeat(60));
  console.log('TEST 4: PREDICT - Ejecutar predicción');
  console.log('='.repeat(60));

  const polygonData = {
    id: 'test_basin_04',
    name: 'Cuenca Test Predicción',
    coordinates: [
      [-75.1847, 4.4378],
      [-75.1247, 4.4378],
      [-75.1247, 4.4978],
      [-75.1847, 4.4978],
      [-75.1847, 4.4378]
    ]
  };

  try {
    const result = await orchestrator.executeE2EPipeline(polygonData, { pipelineId: 'test_predict' });
    const stage = result.stages[Object.keys(PIPELINE_STAGES)[3]];
    
    console.log('\n📋 Resultado:');
    console.log('  - Estado:', stage.status);
    
    if (stage.data?.prediction) {
      console.log('  - Alert Level:', stage.data.prediction.alertLevel);
      console.log('  - Is Fallback:', stage.data.prediction.isFallback || false);
    }
    
    console.log('  - Timestamp:', stage.data?.predictedAt);
    
    if (stage.status === 'COMPLETED') {
      console.log('\n✅ TEST 4 PASÓ: Predicción ejecutada correctamente');
    } else {
      console.log('\n❌ TEST 4 FALLÓ:', stage.error);
    }
    
    return stage.status === 'COMPLETED';
  } catch (error) {
    console.log('\n❌ TEST 4 ERROR:', error.message);
    return false;
  }
}

async function testStage5_Neo4jSave() {
  console.log('\n' + '='.repeat(60));
  console.log('TEST 5: NEO4J_SAVE - Guardar en Neo4j');
  console.log('='.repeat(60));

  const polygonData = {
    id: 'test_basin_05',
    name: 'Cuenca Test Neo4j',
    coordinates: [
      [-75.1847, 4.4378],
      [-75.1247, 4.4378],
      [-75.1247, 4.4978],
      [-75.1847, 4.4978],
      [-75.1847, 4.4378]
    ]
  };

  try {
    const result = await orchestrator.executeE2EPipeline(polygonData, { pipelineId: 'test_neo4j' });
    const stage = result.stages[Object.keys(PIPELINE_STAGES)[4]];
    
    console.log('\n📋 Resultado:');
    console.log('  - Estado:', stage.status);
    console.log('  - Pipeline ID:', stage.data?.pipelineId);
    console.log('  - Timestamp:', stage.data?.savedAt);
    
    if (stage.status === 'COMPLETED') {
      console.log('\n✅ TEST 5 PASÓ: Datos guardados en Neo4j (o fallback)');
    } else {
      console.log('\n❌ TEST 5 FALLÓ:', stage.error);
    }
    
    return stage.status === 'COMPLETED';
  } catch (error) {
    console.log('\n❌ TEST 5 ERROR:', error.message);
    return false;
  }
}

async function testRetryMechanism() {
  console.log('\n' + '='.repeat(60));
  console.log('TEST 6: RETRY MECHANISM - Verificar reintentos automáticos');
  console.log('='.repeat(60));

  const polygonData = {
    id: 'test_retry',
    coordinates: [[-75.1, 4.4], [-75.0, 4.4], [-75.0, 4.5], [-75.1, 4.5], [-75.1, 4.4]]
  };

  const result = await orchestrator.executeE2EPipeline(polygonData, { pipelineId: 'test_retry_pipeline' });
  const pipeline = orchestrator.getPipelineStatus('test_retry_pipeline');

  console.log('\n📋 Resultados del pipeline:');
  console.log('  - Éxito:', result.success);
  console.log('  - Errores:', result.errors.length);

  console.log('\n📋 Estados de etapas:');
  for (const [stageName, stage] of Object.entries(pipeline.stages)) {
    console.log(`  - ${stageName}: ${stage.status} (retry: ${stage.retryCount})`);
  }

  if (result.success) {
    console.log('\n✅ TEST 6 PASÓ: Retry mechanism funciona correctamente');
    return true;
  } else {
    console.log('\n❌ TEST 6 FALLÓ: Pipeline no completó a pesar de reintentos');
    return false;
  }
}

async function testFullE2E() {
  console.log('\n' + '='.repeat(60));
  console.log('TEST 7: E2E COMPLETO - Pipeline completo');
  console.log('='.repeat(60));

  const polygonData = {
    id: 'combeima_full_test',
    name: 'Cuenca Río Combeima - Ibagué',
    type: 'polygon',
    coordinates: [
      [-75.1847, 4.4378],
      [-75.1247, 4.4378],
      [-75.1247, 4.4978],
      [-75.1847, 4.4978],
      [-75.1847, 4.4378]
    ],
    river: 'Río Combeima',
    municipality: 'Ibagué',
    department: 'Tolima',
    country: 'Colombia'
  };

  try {
    const result = await orchestrator.executeE2EPipeline(polygonData, { pipelineId: 'e2e_full_pipeline' });
    
    console.log('\n📋 RESULTADO GENERAL:');
    console.log('  - Pipeline ID:', result.pipelineId);
    console.log('  - Éxito total:', result.success ? '✅ SÍ' : '❌ NO');
    console.log('  - Errores:', result.errors.length);

    console.log('\n📋 DETALLE DE ETAPAS:');
    for (const [stageName, stage] of Object.entries(result.stages)) {
      const icon = stage.status === 'COMPLETED' ? '✅' : stage.status === 'FAILED' ? '❌' : '⏳';
      console.log(`  ${icon} ${stageName}: ${stage.status}`);
    }

    if (result.success) {
      console.log('\n✅ TEST 7 PASÓ: Pipeline E2E completado exitosamente');
    } else {
      console.log('\n❌ TEST 7 FALLÓ:', result.errors);
    }

    return result.success;
  } catch (error) {
    console.log('\n❌ TEST 7 ERROR:', error.message);
    return false;
  }
}

async function runAllTests() {
  console.log('\n' + '#'.repeat(60));
  console.log('# SUITE DE PRUEBAS E2E - SKYFUSION ANALYTICS');
  console.log('# Ibagué - Tareas de Validación y Consistencia Eventual');
  console.log('#'.repeat(60));

  const results = [];

  await orchestrator.initialize({
    analysis: { maxConcurrent: 3, timeout: 10000 },
    prediction: { predictionHorizon: 24, confidenceLevel: 0.95, timeout: 10000 },
    reporting: { modelName: 'gpt-4', temperature: 0.3 },
    retry: { maxRetries: 1, baseDelay: 100 }
  });

  results.push({ name: 'POLYGON_LOAD', pass: await testStage1_PolygonLoad() });
  results.push({ name: 'GEE_INGEST', pass: await testStage2_GEEIngest() });
  results.push({ name: 'VISION_PROCESS', pass: await testStage3_VisionProcess() });
  results.push({ name: 'PREDICT', pass: await testStage4_Predict() });
  results.push({ name: 'NEO4J_SAVE', pass: await testStage5_Neo4jSave() });
  results.push({ name: 'RETRY_MECHANISM', pass: await testRetryMechanism() });
  results.push({ name: 'E2E_COMPLETO', pass: await testFullE2E() });

  console.log('\n' + '='.repeat(60));
  console.log('RESUMEN DE PRUEBAS');
  console.log('='.repeat(60));
  
  let passed = 0;
  let failed = 0;
  
  for (const r of results) {
    const icon = r.pass ? '✅' : '❌';
    console.log(`  ${icon} ${r.name}: ${r.pass ? 'PASÓ' : 'FALLÓ'}`);
    if (r.pass) passed++; else failed++;
  }
  
  console.log('\n' + '-'.repeat(60));
  console.log(`Total: ${results.length} pruebas | ✅ Pasadas: ${passed} | ❌ Fallidas: ${failed}`);
  console.log('='.repeat(60));

  const status = orchestrator.getSystemStatus();
  console.log('\n📊 Estado del Sistema:');
  console.log('  - Inicializado:', status.initialized);
  console.log('  - Pipelines activos:', status.activePipelines);
  console.log('  - Eventos registrados:', status.eventHistory.total);

  await orchestrator.shutdown();

  process.exit(failed > 0 ? 1 : 0);
}

runAllTests();
