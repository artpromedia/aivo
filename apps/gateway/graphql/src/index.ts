import http from 'http';
import path from 'path';

import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import { loadFilesSync } from '@graphql-tools/load-files';
import { mergeTypeDefs } from '@graphql-tools/merge';
import { makeExecutableSchema } from '@graphql-tools/schema';
import compression from 'compression';
import cors from 'cors';
import dotenv from 'dotenv';
import express, { Request, Response } from 'express';
import helmet from 'helmet';


import { JWTAuthService } from './middleware/auth';
import { resolvers } from './resolvers/minimal';
import { RedisCacheService } from './services/cache';
import { User } from './types';

// Load environment variables
dotenv.config();

interface GraphQLContext {
  user?: User;
  authService: JWTAuthService;
  cacheService: RedisCacheService;
  dataloaders: any;
}

async function startServer() {
  const app = express();
  const httpServer = http.createServer(app);

  // Load GraphQL type definitions
  const typeDefs = mergeTypeDefs(
    loadFilesSync(path.join(__dirname, '../schema'), {
      extensions: ['graphql']
    })
  );

  // Create executable schema
  const schema = makeExecutableSchema({
    typeDefs,
    resolvers
  });

  // Initialize services
  const authService = new JWTAuthService({
    secret: process.env.JWT_SECRET || 'your-secret-key',
    issuer: process.env.JWT_ISSUER || 'graphql-gateway',
    audience: process.env.JWT_AUDIENCE || 'aivo-platform'
  });
  const cacheService = new RedisCacheService(
    process.env.REDIS_URL || 'redis://localhost:6379'
  );
  
  // Services will be properly initialized when we need them
  const dataloaders = null; // Will initialize with actual services

  // Create Apollo Server
  const server = new ApolloServer<GraphQLContext>({
    schema,
    plugins: [
      ApolloServerPluginDrainHttpServer({ httpServer }),
    ],
    formatError: (err: any) => {
      console.error('GraphQL Error:', err);
      return err;
    },
    introspection: process.env.NODE_ENV !== 'production',
    includeStacktraceInErrorResponses: process.env.NODE_ENV !== 'production',
  });

  await server.start();

  // Apply middleware
  app.use(helmet());
  app.use(compression());
  app.use(cors({
    origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000'],
    credentials: true,
  }));
  app.use(express.json({ limit: '10mb' }));

  // Health check endpoint
  app.get('/health', (req: Request, res: Response) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // GraphQL endpoint
  app.use('/graphql', expressMiddleware(server, {
    context: async ({ req }: { req: Request }): Promise<GraphQLContext> => {
      const authorization = req.headers.authorization;
      let user: User | undefined;

      if (authorization) {
        try {
          const payload = await authService.verifyToken(authorization.replace('Bearer ', ''));
          // Convert JWTPayload to User
          user = {
            id: payload.sub,
            email: payload.email,
            role: payload.role,
            tenantId: payload.tenantId,
            scopes: payload.scopes,
          };
        } catch (error) {
          // Token invalid, but we don't throw here - let resolvers handle auth
          console.warn('Invalid token:', error);
        }
      }

      return {
        user,
        authService,
        cacheService,
        dataloaders,
      };
    },
  }));

  const port = process.env.PORT || 4000;

  await new Promise<void>((resolve) => {
    httpServer.listen({ port }, resolve);
  });

  console.log(`🚀 GraphQL Gateway ready at http://localhost:${port}/graphql`);
  console.log(`📊 Health check available at http://localhost:${port}/health`);
  
  if (process.env.NODE_ENV !== 'production') {
    console.log(`🔍 GraphQL Playground available at http://localhost:${port}/graphql`);
  }
}

startServer().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
