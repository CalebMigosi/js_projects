import React, {Component} from "react";
import styled from "styled-components";
import Headerbar from "../ui/Headerbar"
export default class DashboardContent extends Component{
    render(){
        return (
            <Content className="dashboard-content">
                <Headerbar></Headerbar>
            </Content>
        )
    }

}

const Content = styled.div`
    height:100vh;
    width: 100%;
    background-color: #19324b;
`