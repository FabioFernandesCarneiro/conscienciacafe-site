/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const { onCall } = require("firebase-functions/v2/https");
const logger = require("firebase-functions/logger");
const admin = require("firebase-admin");

// Inicializar o app do Firebase Admin
admin.initializeApp();

// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

/**
 * Função para excluir um usuário do Firebase Authentication
 * Esta função permite que administradores excluam usuários completamente
 * do sistema, incluindo o Firebase Auth e opcionalmente do Firestore.
 *
 * Parâmetros esperados:
 * - uid: ID do usuário (opcional se email for fornecido)
 * - email: Email do usuário (opcional se uid for fornecido)
 * - deleteFirestore: Se deve excluir os dados do Firestore (padrão: false)
 */
exports.deleteUser = onCall(async (request) => {
  try {
    // Verificar autenticação e permissões
    const auth = request.auth;
    if (!auth) {
      throw new Error("Não autorizado. Você precisa estar autenticado.");
    }

    // Em produção, adicione verificação de admin/role aqui
    // if (!context.auth.token.admin) throw new Error("Permissão negada");

    const data = request.data;
    const uid = data.uid;
    const email = data.email;
    const deleteFirestore = data.deleteFirestore || false;

    logger.info("Tentando excluir usuário", { uid, email });

    let userUid = uid;

    // Se não temos o UID mas temos email, buscar o UID
    if (!userUid && email) {
      try {
        const userRecord = await admin.auth().getUserByEmail(email);
        userUid = userRecord.uid;
        logger.info("UID encontrado para o email", { email, uid: userUid });
      } catch (error) {
        logger.error("Erro ao buscar usuário por email", { email, error });
        const errorMsg = `Usuário com email ${email} não encontrado`;
        throw new Error(`${errorMsg}: ${error.message}`);
      }
    }

    if (!userUid) {
      throw new Error("UID ou email do usuário é necessário");
    }

    // Excluir usuário do Authentication
    await admin.auth().deleteUser(userUid);
    logger.info("Usuário excluído do Firebase Auth", { uid: userUid });

    // Se solicitado, excluir também do Firestore
    if (deleteFirestore) {
      await admin.firestore().collection("users").doc(userUid).delete();
      logger.info("Usuário excluído do Firestore", { uid: userUid });
    }

    return { success: true, message: "Usuário excluído com sucesso" };
  } catch (error) {
    logger.error("Erro ao excluir usuário", { error });
    throw new Error(`Falha ao excluir usuário: ${error.message}`);
  }
});

/**
 * Função para criar um novo usuário no Firebase Auth sem afetar a sessão atual
 *
 * Parâmetros esperados:
 * - email: Email do usuário a ser criado
 * - password: Senha do usuário
 * - displayName: Nome de exibição do usuário (opcional)
 */
exports.createUser = onCall(async (request) => {
  try {
    // Verificar autenticação e permissões
    const auth = request.auth;
    if (!auth) {
      throw new Error("Não autorizado. Você precisa estar autenticado.");
    }

    // Em produção, adicione verificação de admin/role aqui
    // if (!context.auth.token.admin) throw new Error("Permissão negada");

    const data = request.data;
    const email = data.email;
    const password = data.password;
    const displayName = data.displayName;

    if (!email || !password) {
      throw new Error("Email e senha são obrigatórios");
    }

    logger.info("Tentando criar usuário", { email, displayName });

    // Verificar se o usuário já existe
    try {
      const userRecord = await admin.auth().getUserByEmail(email);
      if (userRecord) {
        throw new Error(`Usuário com email ${email} já existe`);
      }
    } catch (error) {
      // Se o erro for not-found, é o que queremos - o usuário não existe
      if (error.code !== "auth/user-not-found") {
        throw error;
      }
    }

    // Criar o usuário no Firebase Auth utilizando o Admin SDK
    const userRecord = await admin.auth().createUser({
      email,
      password,
      displayName,
      emailVerified: false,
    });

    logger.info("Usuário criado com sucesso", { uid: userRecord.uid });

    return {
      success: true,
      message: "Usuário criado com sucesso",
      uid: userRecord.uid,
    };
  } catch (error) {
    logger.error("Erro ao criar usuário", { error });
    throw new Error(`Falha ao criar usuário: ${error.message}`);
  }
});
