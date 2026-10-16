export const companyQuestions = [
  "Who owns Session Broker?",
  "Who owns Token Cache?",
  "What would replacing Auth Gateway affect?",
  "Which projects use Billing API?",
];

export function questionFor(intent: string, name: string) {
  const shapes: Record<string, string> = {
    owners: "Who owns SERVICE?",
    dependents: "What would replacing SERVICE affect?",
    projects: "Which projects use SERVICE?",
    reviewers: "Who should review a change to SERVICE?",
    documents: "What documents mention SERVICE?",
  };
  return (shapes[intent] || shapes.owners).replace("SERVICE", name);
}
