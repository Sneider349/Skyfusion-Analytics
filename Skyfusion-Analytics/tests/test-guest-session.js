/**
 * Script de prueba para la sesión de invitado
 */

const http = require('http');

const API_URL = process.env.API_URL || 'http://localhost:3000';

function makeRequest(method, path, data = null, token = null) {
    return new Promise((resolve, reject) => {
        const url = new URL(path, API_URL);
        
        const options = {
            hostname: url.hostname,
            port: url.port || 3000,
            path: url.pathname,
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }
        
        const req = http.request(options, (res) => {
            let body = '';
            
            res.on('data', (chunk) => {
                body += chunk;
            });
            
            res.on('end', () => {
                try {
                    resolve({
                        status: res.statusCode,
                        data: JSON.parse(body)
                    });
                } catch (e) {
                    resolve({
                        status: res.statusCode,
                        data: body
                    });
                }
            });
        });
        
        req.on('error', reject);
        
        if (data) {
            req.write(JSON.stringify(data));
        }
        
        req.end();
    });
}

async function testGuestSession() {
    console.log('🧪 Iniciando pruebas de sesión de invitado...\n');
    
    console.log('1️⃣  Probando endpoint de información de la API...');
    try {
        const apiInfo = await makeRequest('GET', '/api/info');
        console.log('   ✅ API Info:', apiInfo.data.name);
        console.log('   ✅ Roles disponibles:', Object.keys(apiInfo.data.roles).join(', '));
    } catch (error) {
        console.log('   ❌ Error:', error.message);
    }
    
    console.log('\n2️⃣  Creando sesión de invitado...');
    try {
        const guestResponse = await makeRequest('POST', '/api/auth/guest');
        
        if (guestResponse.status === 201) {
            console.log('   ✅ Sesión de invitado creada');
            console.log('   ✅ Token recibido:', guestResponse.data.token.substring(0, 50) + '...');
            console.log('   ✅ Usuario:', guestResponse.data.user.username);
            console.log('   ✅ Rol:', guestResponse.data.user.role);
            console.log('   ✅ Permisos:', JSON.stringify(guestResponse.data.permissions, null, 2));
            
            const token = guestResponse.data.token;
            
            console.log('\n3️⃣  Probando acceso a predicciones con sesión de invitado...');
            const predictions = await makeRequest('GET', '/api/predictions/COMBEIMA', null, token);
            console.log('   ✅ Acceso a predicciones:', predictions.data.is_guest_access ? 'Sí (invitado)' : 'No');
            
            console.log('\n4️⃣  Probando acceso a alertas...');
            const alerts = await makeRequest('GET', '/api/alerts', null, token);
            console.log('   ✅ Acceso a alertas:', alerts.data.is_guest_access ? 'Sí (invitado)' : 'No');
            console.log('   ✅ Noticia para invitado:', alerts.data.guest_notice || 'Ninguna');
            
            console.log('\n5️⃣  Probando endpoint protegido (crear notificación de prueba)...');
            const testNotification = await makeRequest('POST', '/api/notifications/test', {
                title: 'Prueba',
                message: 'Esto debería fallar para invitado'
            }, token);
            
            if (testNotification.status === 403) {
                console.log('   ✅ Acceso denegado correctamente (como esperado)');
                console.log('   ❌ Código de error:', testNotification.data.code);
                console.log('   ❌ Mensaje:', testNotification.data.error);
                console.log('   💡 Sugerencia:', testNotification.data.suggestion);
            } else {
                console.log('   ⚠️  Status:', testNotification.status);
            }
            
            console.log('\n6️⃣  Verificando expiración de sesión...');
            console.log('   📅 Expira en:', new Date(guestResponse.data.user.expiresAt).toLocaleString());
            
        } else {
            console.log('   ❌ Error al crear sesión:', guestResponse.data);
        }
    } catch (error) {
        console.log('   ❌ Error:', error.message);
    }
    
    console.log('\n7️⃣  Comparando con usuario registrado (admin)...');
    try {
        const loginResponse = await makeRequest('POST', '/api/auth/login', {
            email: 'admin@skyfusion.com',
            password: 'admin123'
        });
        
        if (loginResponse.status === 200) {
            console.log('   ✅ Login exitoso');
            console.log('   ✅ Permisos admin:', JSON.stringify(loginResponse.data.permissions, null, 2));
            
            const adminToken = loginResponse.data.token;
            
            console.log('\n8️⃣  Probando endpoint protegido con admin...');
            const testNotification = await makeRequest('POST', '/api/notifications/test', {
                title: 'Prueba Admin',
                message: 'Esto debería funcionar para admin'
            }, adminToken);
            
            if (testNotification.status === 200 || testNotification.status === 201) {
                console.log('   ✅ Admin puede crear notificaciones');
            } else {
                console.log('   ⚠️  Status:', testNotification.status);
            }
        } else {
            console.log('   ⚠️  No se pudo hacer login con admin (posiblemente credenciales incorrectas)');
        }
    } catch (error) {
        console.log('   ⚠️  Error:', error.message);
    }
    
    console.log('\n9️⃣  Probando acceso sin autenticación...');
    try {
        const publicData = await makeRequest('GET', '/api/predictions/COMBEIMA');
        console.log('   ✅ Acceso público a predicciones:', publicData.data.catchment_id);
    } catch (error) {
        console.log('   ❌ Error:', error.message);
    }
    
    console.log('\n✅ Pruebas completadas!\n');
}

console.log('🚀 Script de prueba de sesión de invitado\n');
console.log('📝 Asegúrate de que el servidor esté corriendo en:', API_URL);
console.log('   Ejecuta: npm run dev\n');

testGuestSession().catch(console.error);
