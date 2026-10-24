
| Action                                                     | owner         | security_admin | team_admin | member   | auditor |
| ---------------------------------------------------------- | ------------- | -------------- | ---------- | -------- | ------- |
| Add members and change roles                               | ✔ (any role) | ✔ (not owner) | ✘         | ✘       | ✘      |
| See the member list                                        | ✔            | ✔             | ✔         | ✘       | ✔      |
| Read and write**shared**org documents                | ✔            | ✘             | ✔         | ✔       | ✘      |
| Delete shared documents                                    | any           | ✘             | any        | own only | ✘      |
| Read the org audit log                                     | ✔            | ✔             | ✘         | ✘       | ✔      |
| Read someone’s**private**chats, documents or memory | ✘            | ✘             | ✘         | ✘       | ✘      |

The last row has no ✔ for anyone. Admin roles manage people but don’t get document content, even shared content. Break-glass (exceptional, approved and audited access) comes in Phase 10.
