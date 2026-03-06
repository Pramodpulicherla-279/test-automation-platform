import api from "../api/axiosConfig";

const issueService = {

  getIssues: async () => {
    const response = await api.get("/issues");
    return response.data;
  },

  updateIssue: async (id, data) => {
    const response = await api.put(`/issues/${id}`, data);
    return response.data;
  },

  createTicket: async (id) => {
    const response = await api.post("/create-ticket", { id });
    return response.data;
  },

  getHistory: async () => {
    const response = await api.get("/history");
    return response.data;
  }

};

export default issueService;