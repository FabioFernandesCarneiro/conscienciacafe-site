/**
 * Script para adicionar usuário admin no Firebase Realtime Database
 *
 * Uso: node scripts/add-admin-user.js
 */

const admin = require('firebase-admin');

// Inicializa o Firebase Admin com as credenciais padrão do projeto
admin.initializeApp({
  databaseURL: 'https://conscienciacafe-default-rtdb.firebaseio.com'
});

const db = admin.database();

const userData = {
  email: 'fabiofernandescarneiro@gmail.com',
  name: 'Fabio Carneiro',
  role: 'gestor',
  active: true,
  createdAt: new Date().toISOString(),
  createdBy: 'Qpzmot04I2XFRt8ulInOfPuqoei2'
};

const userId = 'Qpzmot04I2XFRt8ulInOfPuqoei2';

async function addAdminUser() {
  try {
    console.log('Adicionando usuário admin...');
    console.log('UID:', userId);
    console.log('Dados:', JSON.stringify(userData, null, 2));

    await db.ref(`users/${userId}`).set(userData);

    console.log('\n✅ Usuário admin criado com sucesso!');
    console.log('Email:', userData.email);
    console.log('Role:', userData.role);

    process.exit(0);
  } catch (error) {
    console.error('\n❌ Erro ao criar usuário:', error.message);
    process.exit(1);
  }
}

addAdminUser();
