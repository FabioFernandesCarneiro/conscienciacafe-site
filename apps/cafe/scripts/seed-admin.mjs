/**
 * Script para criar usuários admin no Firebase usando Admin SDK
 *
 * SETUP:
 * 1. Vá no Firebase Console > Project Settings > Service Accounts
 * 2. Clique em "Generate new private key"
 * 3. Salve o arquivo como: scripts/serviceAccountKey.json
 * 4. Rode: node scripts/seed-admin.mjs
 *
 * IMPORTANTE: Nunca commite o serviceAccountKey.json!
 */

import { initializeApp, cert } from 'firebase-admin/app';
import { getDatabase } from 'firebase-admin/database';
import { readFileSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const serviceAccountPath = join(__dirname, 'serviceAccountKey.json');

// Verificar se o arquivo de credenciais existe
if (!existsSync(serviceAccountPath)) {
  console.error('❌ Arquivo serviceAccountKey.json não encontrado!');
  console.log('');
  console.log('📝 Para obter o arquivo:');
  console.log('   1. Vá no Firebase Console > Project Settings > Service Accounts');
  console.log('   2. Clique em "Generate new private key"');
  console.log('   3. Salve o arquivo como: scripts/serviceAccountKey.json');
  console.log('');
  process.exit(1);
}

// Carregar credenciais
const serviceAccount = JSON.parse(readFileSync(serviceAccountPath, 'utf8'));

// Inicializar Firebase Admin
const app = initializeApp({
  credential: cert(serviceAccount),
  databaseURL: 'https://conscienciacafe-default-rtdb.firebaseio.com',
});

const db = getDatabase(app);

// Dados do admin a ser criado
const adminUsers = [
  {
    uid: 'Qpzmot04I2XFRt8ulInOfPuqoei2',
    data: {
      email: 'fabiofernandescarneiro@gmail.com',
      name: 'Fabio Carneiro',
      role: 'gestor',
      active: true,
      createdAt: new Date().toISOString(),
      createdBy: 'seed-script',
    },
  },
];

async function seedAdmins() {
  console.log('🌱 Iniciando seed de usuários admin...');
  console.log('');

  for (const admin of adminUsers) {
    try {
      console.log(`📝 Criando usuário: ${admin.data.name}`);
      console.log(`   Email: ${admin.data.email}`);
      console.log(`   Role: ${admin.data.role}`);
      console.log(`   UID: ${admin.uid}`);

      await db.ref(`users/${admin.uid}`).set(admin.data);

      console.log(`   ✅ Criado com sucesso!`);
      console.log('');
    } catch (error) {
      console.error(`   ❌ Erro: ${error.message}`);
      console.log('');
    }
  }

  console.log('🎉 Seed concluído!');
  console.log('');
  console.log('Agora você pode fazer login em: http://localhost:3001/login');

  process.exit(0);
}

seedAdmins();
