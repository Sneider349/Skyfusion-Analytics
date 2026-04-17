/**
 * Rutas de Reportes
 */

const express = require('express');
const router = express.Router();

router.post('/pdf', async (req, res, next) => {
    try {
        const { catchment_id, start_date, end_date, sections } = req.body;

        res.json({
            status: 'generating',
            report_id: `report-${Date.now()}`,
            catchment_id,
            date_range: { start: start_date, end: end_date },
            estimated_time: '30 segundos',
            download_url: `/api/v1/reports/pdf/download/report-${Date.now()}.pdf`
        });
    } catch (error) {
        next(error);
    }
});

router.post('/excel', async (req, res, next) => {
    try {
        const { catchment_id, start_date, end_date, data_types } = req.body;

        res.json({
            status: 'generating',
            report_id: `excel-${Date.now()}`,
            catchment_id,
            date_range: { start: start_date, end: end_date },
            estimated_time: '15 segundos',
            download_url: `/api/v1/reports/excel/download/excel-${Date.now()}.xlsx`
        });
    } catch (error) {
        next(error);
    }
});

module.exports = router;
