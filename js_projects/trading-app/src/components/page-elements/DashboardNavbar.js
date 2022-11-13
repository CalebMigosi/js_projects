import React, {Component} from "react";
import styled from 'styled-components'
import { Link } from 'react-router-dom';
import StockTicks from "../../assets/img/stocks.svg"
import BurgerMenu from "../../assets/img/menu.svg"

export default class DashboardNavbar extends Component{
    constructor(props){
        super(props)

        // Define state values
        this.state = {
            barOpened: false,
            isActive: false
        }
    }

    render(){
        return (
            <Navbar className = "dashboard-navbar" barOpened = {this.state.barOpened}>
                <Link to="/"><BurgerMenuImg src= {BurgerMenu}></BurgerMenuImg></Link>
                <Link to="/test"><Image src= {StockTicks}></Image></Link>
                <Link to="/test"><Image src= {StockTicks}></Image></Link>
                <Link to="/test"><Image src= {StockTicks}></Image></Link>
                <Link to="/test"><Image src= {StockTicks}></Image></Link>
            </Navbar>)
    }
}

const Navbar = styled.div`
    padding: 1rem;
    margin-top: 10vh;
    background-color: black;
    height: 100vh;
    width: 10vw;
    display: flex;
    flex-direction: column;
    gap: 10vh;
    align-items: center;
`

const BurgerMenuImg = styled.img`
    height: 2rem;
    width: 2rem;
`

BurgerMenuImg.defaultProps = {
    src: BurgerMenu,
}

const Image = styled.img`
    height: 3rem;
    width: 3rem;
    filter: ${props => (props.isActive ? "grayscale(0%)" :"grayscale(100%)")};
`

Image.defaultProps = {
    src: StockTicks,
}