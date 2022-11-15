import React from "react";
import styled from "styled-components";
import Headerbar from "../ui/Headerbar";

export default function DashboardContent(props){
    return (
        <Content className="dashboard-content">
            <Headerbar></Headerbar>
            {props.children}
        </Content>
    )
}

const Content = styled.div`
    min-height: 50%;
    height:100%;
    width: 100%;
    background-color: #19324b;
`