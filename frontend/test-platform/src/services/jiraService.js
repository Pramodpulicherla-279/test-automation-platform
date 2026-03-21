import api from "../api/axiosConfig";

const jiraService = {

  createTicket: async (issueData) => {
    

    const response = await api.post("/create-ticket", issueData);

    return response.data;

  }

};

export default jiraService;