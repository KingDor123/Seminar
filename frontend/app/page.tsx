import ChatInterface from "../components/ChatInterface";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-col items-center w-full max-w-4xl p-4">
        <h1 className="text-3xl font-bold mb-8 text-gray-800 dark:text-gray-100">SoftSkill AI Coach</h1>
        <ChatInterface />
      </main>
    </div>
  );
}
